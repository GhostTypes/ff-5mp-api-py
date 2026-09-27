"""
Uploads must not block the event loop and must not time out on large files.

Home Assistant reports a blocking ``open()`` on its event loop as an error, and
a 500 MB job over printer Wi-Fi takes longer than aiohttp's default five-minute
request cap. Each upload method therefore opens and sizes the file in a worker
thread and uses UPLOAD_TIMEOUT, which has no total cap.
"""

import builtins
import threading
from unittest.mock import AsyncMock, patch

import pytest

from flashforge.api.controls import job_control as job_control_module
from flashforge.api.controls.job_control import UPLOAD_TIMEOUT
from flashforge.models import AD5XMaterialMapping, AD5XUploadParams, Creator5UploadParams
from tests.test_job_control import _build_client, _mock_session

MAPPING = AD5XMaterialMapping(
    tool_id=0,
    slot_id=1,
    material_name="PLA",
    tool_material_color="#FFFFFF",
    slot_material_color="#FFFFFF",
)


async def _run_upload(kind, client, file_path):
    job_control = client.job_control
    if kind == "generic":
        return await job_control.upload_file(file_path, True, False)
    if kind == "ad5x":
        return await job_control.upload_file_ad5x(
            AD5XUploadParams(
                file_path=file_path,
                start_print=True,
                leveling_before_print=False,
                flow_calibration=False,
                first_layer_inspection=False,
                time_lapse_video=False,
                material_mappings=[MAPPING],
            )
        )
    return await job_control.upload_file_creator5(
        Creator5UploadParams(
            file_path=file_path,
            start_print=False,
            leveling_before_print=False,
            use_matl_station=True,
            gcode_tool_cnt=1,
        )
    )


def _client_for(kind):
    client = _build_client()
    client.firmware_ver = "3.2.0"
    if kind == "ad5x":
        client._is_ad5x = True
    if kind == "creator5":
        client.is_creator5 = True
    return client


@pytest.mark.parametrize("kind", ["generic", "ad5x", "creator5"])
async def test_upload_opens_the_file_off_the_event_loop(tmp_path, kind):
    test_file = tmp_path / "job.3mf"
    test_file.write_bytes(b"PK\x03\x04 test")
    client = _client_for(kind)

    loop_thread = threading.current_thread()
    open_threads: list[threading.Thread] = []
    real_open = builtins.open

    def tracking_open(*args, **kwargs):
        open_threads.append(threading.current_thread())
        return real_open(*args, **kwargs)

    mock_session, _ = _mock_session({"code": 0, "message": "Success"})
    with (
        patch("aiohttp.ClientSession", return_value=mock_session) as session_cls,
        patch.object(job_control_module, "open", tracking_open, create=True),
        patch("flashforge.api.controls.job_control.NetworkUtils.is_ok", return_value=True),
    ):
        result = await _run_upload(kind, client, str(test_file))

    assert result is True
    assert open_threads, "the upload never opened the file"
    assert all(thread is not loop_thread for thread in open_threads)
    assert session_cls.call_args.kwargs["timeout"] is UPLOAD_TIMEOUT


def test_upload_timeout_has_no_total_cap():
    assert UPLOAD_TIMEOUT.total is None
    assert UPLOAD_TIMEOUT.sock_connect == 30
    assert UPLOAD_TIMEOUT.sock_read == 300


async def test_directory_is_not_uploaded(tmp_path):
    client = _client_for("generic")
    post = AsyncMock()
    with patch("aiohttp.ClientSession", post):
        result = await client.job_control.upload_file(str(tmp_path), True, False)

    assert result is False
    post.assert_not_called()
