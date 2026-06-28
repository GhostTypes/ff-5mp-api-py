"""
Unit tests for Creator 5 / Creator 5 Pro job control + the isNewFirmware fix.

Mirrors src/api/controls/JobControl.test.ts (printLocalFile new-firmware
short-circuit + startCreator5Job section), plus Creator 5 upload and AD5X
upload regression coverage.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flashforge.api.constants.endpoints import Endpoints
from flashforge.client import FlashForgeClient
from flashforge.models.responses import AD5XMaterialMapping, Creator5JobParams, Creator5UploadParams


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
    """Create a FlashForgeClient with a mocked TCP client."""
    client = FlashForgeClient("192.168.1.120", "SN123456", "CC123456")
    client.tcp_client = MagicMock()
    return client


# ---------------------------------------------------------------------------
# _is_new_firmware_version short-circuit for AD5X / Creator 5.
# ---------------------------------------------------------------------------
def test_is_new_firmware_short_circuits_for_creator5():
    """The C5 reports a 1.x version the numeric check would misread as 'old'."""
    client = _build_client()
    client.is_creator5 = True
    client.firmware_ver = "1.9.2"

    assert client.job_control._is_new_firmware_version() is True


def test_is_new_firmware_short_circuits_for_creator5_pro():
    """The Creator 5 Pro also short-circuits to the new payload format."""
    client = _build_client()
    client.is_creator5_pro = True
    client.is_creator5 = True
    client.firmware_ver = "1.0.5"

    assert client.job_control._is_new_firmware_version() is True


def test_is_new_firmware_short_circuits_for_ad5x():
    """The AD5X always uses the new payload format regardless of version."""
    client = _build_client()
    client._is_ad5x = True  # noqa: SLF001 - read-only property backing field
    client.firmware_ver = "1.1.7"

    assert client.job_control._is_new_firmware_version() is True


def test_is_new_firmware_numeric_compare_still_applies_to_5m():
    """The numeric 3.1.3 threshold still applies to the 5M family."""
    client = _build_client()
    client.firmware_ver = "3.1.2"

    assert client.job_control._is_new_firmware_version() is False

    client.firmware_ver = "3.1.3"
    assert client.job_control._is_new_firmware_version() is True


# ---------------------------------------------------------------------------
# start_creator5_job -- POST /printGcode with the C5-native body.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_start_creator5_job_multi_tool_body():
    """POSTs the Creator 5-native /printGcode body matching the captured shape."""
    client = _build_client()
    client.is_creator5 = True
    mock_session, _ = _mock_session({"code": 0, "message": "Success"})

    mappings = [
        AD5XMaterialMapping(
            tool_id=0,
            slot_id=2,
            material_name="PLA",
            tool_material_color="#2E54DD",
            slot_material_color="#2E54DD",
        ),
        AD5XMaterialMapping(
            tool_id=1,
            slot_id=3,
            material_name="PETG",
            tool_material_color="#FF0000",
            slot_material_color="#FF0000",
        ),
    ]

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.job_control.NetworkUtils.is_ok", return_value=True):
            result = await client.job_control.start_creator5_job(
                Creator5JobParams(
                    file_name="multi.3mf",
                    leveling_before_print=True,
                    material_mappings=mappings,
                )
            )

    assert result is True
    url = mock_session.post.call_args.args[0]
    assert url == f"http://192.168.1.120:8898{Endpoints.GCODE_PRINT}"
    body = mock_session.post.call_args.kwargs["json"]
    # Confirmed C5 capture: flowCalibration/timeLapseVideo always present,
    # mappings carry colors (same shape as AD5X), and no useMatlStation /
    # gcodeToolCnt / firstLayerInspection.
    assert body == {
        "serialNumber": "SN123456",
        "checkCode": "CC123456",
        "fileName": "multi.3mf",
        "levelingBeforePrint": True,
        "flowCalibration": False,
        "timeLapseVideo": False,
        "materialMappings": [
            {
                "toolId": 0,
                "slotId": 2,
                "materialName": "PLA",
                "toolMaterialColor": "#2E54DD",
                "slotMaterialColor": "#2E54DD",
            },
            {
                "toolId": 1,
                "slotId": 3,
                "materialName": "PETG",
                "toolMaterialColor": "#FF0000",
                "slotMaterialColor": "#FF0000",
            },
        ],
    }
    assert "useMatlStation" not in body
    assert "gcodeToolCnt" not in body
    assert "firstLayerInspection" not in body


@pytest.mark.asyncio
async def test_start_creator5_job_single_tool_omits_material_mappings():
    """Single-tool C5 print omits materialMappings from the body."""
    client = _build_client()
    client.is_creator5 = True
    mock_session, _ = _mock_session({"code": 0, "message": "Success"})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.job_control.NetworkUtils.is_ok", return_value=True):
            result = await client.job_control.start_creator5_job(
                Creator5JobParams(file_name="single.gcode", leveling_before_print=False)
            )

    assert result is True
    body = mock_session.post.call_args.kwargs["json"]
    assert "materialMappings" not in body
    assert body["flowCalibration"] is False
    assert body["timeLapseVideo"] is False


@pytest.mark.asyncio
async def test_start_creator5_job_rejects_empty_material_name():
    """An empty materialName is rejected without calling the printer.

    Pydantic enforces slotId/toolId ranges and the color regex at construction,
    so the only ``_validate_creator5_material_mappings`` branch reachable from
    ``start_creator5_job`` is the non-empty materialName check. A whitespace-only
    name passes pydantic (the field has no min_length) and is caught by the
    shared validator's ``.strip()`` check.
    """
    client = _build_client()
    client.is_creator5 = True
    mock_session, _ = _mock_session({"code": 0, "message": "Success"})

    mappings = [
        AD5XMaterialMapping(
            tool_id=0,
            slot_id=1,
            material_name="   ",  # whitespace-only -> stripped to empty
            tool_material_color="#2E54DD",
            slot_material_color="#2E54DD",
        )
    ]

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await client.job_control.start_creator5_job(
            Creator5JobParams(
                file_name="multi.3mf",
                leveling_before_print=True,
                material_mappings=mappings,
            )
        )

    assert result is False
    # The printer was never contacted.
    mock_session.post.assert_not_called()


@pytest.mark.asyncio
async def test_start_creator5_job_refuses_non_material_station_printer():
    """start_creator5_job refuses to run on a non-material-station printer."""
    client = _build_client()
    client.is_creator5 = False
    client._is_ad5x = False  # noqa: SLF001
    mock_session, _ = _mock_session({"code": 0, "message": "Success"})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await client.job_control.start_creator5_job(
            Creator5JobParams(file_name="x.gcode", leveling_before_print=True)
        )

    assert result is False
    mock_session.post.assert_not_called()


# ---------------------------------------------------------------------------
# upload_file_creator5 -- POST /uploadGcode with C5 headers (no firstLayerInspection).
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_upload_file_creator5_headers(tmp_path):
    """C5 upload sends useMatlStation/gcodeToolCnt but NO firstLayerInspection."""
    client = _build_client()
    client.is_creator5 = True
    test_file = tmp_path / "multi.3mf"
    test_file.write_bytes(b"binary gcode")

    mock_session, _ = _mock_session({"code": 0, "message": "Success"})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.job_control.NetworkUtils.is_ok", return_value=True):
            result = await client.job_control.upload_file_creator5(
                Creator5UploadParams(
                    file_path=str(test_file),
                    start_print=False,
                    leveling_before_print=True,
                    flow_calibration=True,
                    time_lapse_video=False,
                    use_matl_station=True,
                    gcode_tool_cnt=2,
                )
            )

    assert result is True
    headers = mock_session.post.call_args.kwargs["headers"]
    assert headers["serialNumber"] == "SN123456"
    assert headers["useMatlStation"] == "true"
    assert headers["gcodeToolCnt"] == "2"
    assert headers["flowCalibration"] == "true"
    assert headers["timeLapseVideo"] == "false"
    assert headers["printNow"] == "false"
    # The C5 has no firstLayerInspection field and maps materials at print-start.
    assert "firstLayerInspection" not in headers
    assert "materialMappings" not in headers


@pytest.mark.asyncio
async def test_upload_file_creator5_missing_file(tmp_path):
    """upload_file_creator5 returns False when the local file is missing."""
    client = _build_client()
    client.is_creator5 = True
    missing = tmp_path / "missing.gcode"

    result = await client.job_control.upload_file_creator5(
        Creator5UploadParams(
            file_path=str(missing),
            start_print=False,
            leveling_before_print=False,
            use_matl_station=False,
            gcode_tool_cnt=1,
        )
    )

    assert result is False


# ---------------------------------------------------------------------------
# AD5X upload regression guard -- still includes firstLayerInspection.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_upload_file_ad5x_still_includes_first_layer_inspection(tmp_path):
    """AD5X upload keeps the firstLayerInspection header (C5 does not)."""
    from flashforge.models.responses import AD5XUploadParams

    client = _build_client()
    client._is_ad5x = True  # noqa: SLF001
    test_file = tmp_path / "ad5x.3mf"
    test_file.write_bytes(b"binary gcode")

    mock_session, _ = _mock_session({"code": 0, "message": "Success"})

    mappings = [
        AD5XMaterialMapping(
            tool_id=0,
            slot_id=1,
            material_name="PLA",
            tool_material_color="#FF0000",
            slot_material_color="#FF0000",
        )
    ]

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.job_control.NetworkUtils.is_ok", return_value=True):
            result = await client.job_control.upload_file_ad5x(
                AD5XUploadParams(
                    file_path=str(test_file),
                    start_print=False,
                    leveling_before_print=True,
                    flow_calibration=False,
                    first_layer_inspection=True,
                    time_lapse_video=False,
                    material_mappings=mappings,
                )
            )

    assert result is True
    headers = mock_session.post.call_args.kwargs["headers"]
    assert headers["firstLayerInspection"] == "true"
    assert headers["useMatlStation"] == "true"
    assert "materialMappings" in headers  # AD5X base64-encodes mappings at upload
