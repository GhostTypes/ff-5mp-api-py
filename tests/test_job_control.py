"""
Unit tests for job control operations.
"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from flashforge.client import FlashForgeClient
from flashforge.api.controls.job_control import JobControl


def _mock_session(response_payload: dict, status: int = 200):
    """Build a mocked aiohttp session returning the provided payload."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=response_payload)
    mock_response.text = AsyncMock(return_value=json.dumps(response_payload))

    mock_post_ctx = MagicMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=mock_post_ctx)

    return mock_session, mock_response


def _build_client() -> FlashForgeClient:
    """Create a FlashForgeClient instance with patched TCP client."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.tcp_client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_pause_print_job_success():
    """pause_print_job delegates to control.send_job_control_cmd."""
    client = _build_client()
    job_control = JobControl(client)
    job_control._control = Mock()
    job_control._control.send_job_control_cmd = AsyncMock(return_value=True)

    result = await job_control.pause_print_job()

    assert result is True
    job_control._control.send_job_control_cmd.assert_awaited_once_with("pause")


@pytest.mark.asyncio
async def test_pause_print_job_when_idle():
    """pause_print_job returns False when control rejects command."""
    client = _build_client()
    job_control = JobControl(client)
    job_control._control = Mock()
    job_control._control.send_job_control_cmd = AsyncMock(return_value=False)

    result = await job_control.pause_print_job()

    assert result is False


@pytest.mark.asyncio
async def test_resume_print_job_success():
    """resume_print_job sends continue command."""
    client = _build_client()
    job_control = JobControl(client)
    job_control._control = Mock()
    job_control._control.send_job_control_cmd = AsyncMock(return_value=True)

    result = await job_control.resume_print_job()

    assert result is True
    job_control._control.send_job_control_cmd.assert_awaited_once_with("continue")


@pytest.mark.asyncio
async def test_cancel_print_job_success():
    """cancel_print_job sends cancel command."""
    client = _build_client()
    job_control = JobControl(client)
    job_control._control = Mock()
    job_control._control.send_job_control_cmd = AsyncMock(return_value=True)

    result = await job_control.cancel_print_job()

    assert result is True
    job_control._control.send_job_control_cmd.assert_awaited_once_with("cancel")


@pytest.mark.asyncio
async def test_upload_file_success(tmp_path):
    """upload_file uploads file with correct headers for new firmware."""
    client = _build_client()
    client.firmware_ver = "3.2.0"
    job_control = client.job_control

    test_file = tmp_path / "cube.gcode"
    test_file.write_text("G1 X0 Y0\n")

    from tests.fixtures.printer_responses import PRODUCT_RESPONSE

    mock_session, mock_response = _mock_session(PRODUCT_RESPONSE)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.job_control.NetworkUtils.is_ok", return_value=True):
            result = await job_control.upload_file(str(test_file), True, False)

    assert result is True
    mock_response.json.assert_awaited()
    assert mock_session.post.call_count == 1

    kwargs = mock_session.post.call_args.kwargs
    headers = kwargs["headers"]
    assert headers["serialNumber"] == "SN123"
    assert headers["printNow"] == "true"
    assert headers["flowCalibration"] == "false"
    assert headers["useMatlStation"] == "false"


@pytest.mark.asyncio
async def test_upload_file_not_found(tmp_path):
    """upload_file returns False when local file missing."""
    client = _build_client()
    job_control = client.job_control
    missing = tmp_path / "missing.gcode"

    result = await job_control.upload_file(str(missing), False, False)

    assert result is False


@pytest.mark.asyncio
async def test_print_local_file_new_firmware():
    """print_local_file uses extended payload for firmware >= 3.1.3."""
    client = _build_client()
    client.firmware_ver = "3.1.3"
    job_control = client.job_control

    from flashforge.api.controls.job_control import NetworkUtils

    mock_session, mock_response = _mock_session({"code": 0})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch.object(NetworkUtils, "is_ok", return_value=True):
            result = await job_control.print_local_file("cube.gcode", True)

    assert result is True
    payload = mock_session.post.call_args.kwargs["json"]
    assert payload["useMatlStation"] is False
    assert payload["flowCalibration"] is False
    assert payload["fileName"] == "cube.gcode"


@pytest.mark.asyncio
async def test_print_local_file_old_firmware():
    """print_local_file uses legacy payload for firmware < 3.1.3."""
    client = _build_client()
    client.firmware_ver = "3.1.2"
    job_control = client.job_control

    from flashforge.api.controls.job_control import NetworkUtils

    mock_session, _ = _mock_session({"code": 0})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch.object(NetworkUtils, "is_ok", return_value=True):
            result = await job_control.print_local_file("cube.gcode", False)

    assert result is True
    payload = mock_session.post.call_args.kwargs["json"]
    assert "useMatlStation" not in payload
    assert payload["levelingBeforePrint"] is False


def test_is_new_firmware_version_true():
    """_is_new_firmware_version correctly detects new firmware."""
    client = _build_client()
    job_control = client.job_control
    client.firmware_ver = "3.1.4"

    assert job_control._is_new_firmware_version() is True
    client.firmware_ver = "4.0.0"
    assert job_control._is_new_firmware_version() is True


def test_is_new_firmware_version_false():
    """_is_new_firmware_version detects old firmware versions."""
    client = _build_client()
    job_control = client.job_control
    client.firmware_ver = "3.1.2"

    assert job_control._is_new_firmware_version() is False
    client.firmware_ver = "3.0.9"
    assert job_control._is_new_firmware_version() is False
