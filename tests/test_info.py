"""
Unit tests for the Info module.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flashforge.api.constants.endpoints import Endpoints
from flashforge.api.controls.info import Info, MachineInfoParser
from flashforge.client import FlashForgeClient
from flashforge.exceptions import FlashForgeResponseError
from flashforge.models import FFMachineInfo, MachineState
from flashforge.models.responses import DetailResponse
from tests.fixtures.printer_responses import (
    AD5X_INFO_RESPONSE,
    FIVE_M_PRO_INFO_RESPONSE,
)


def _mock_session(response_payload: dict, status: int = 200):
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
    return mock_session


def _build_info() -> Info:
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.tcp_client = AsyncMock()
    return client.info


@pytest.mark.asyncio
async def test_get_info_success_ad5x():
    """get() returns FFMachineInfo for AD5X details."""
    info = _build_info()
    detail_response = DetailResponse(**AD5X_INFO_RESPONSE)
    info.get_detail_response = AsyncMock(return_value=detail_response)

    machine_info = await info.get()

    assert isinstance(machine_info, FFMachineInfo)
    assert machine_info.is_ad5x is True
    assert machine_info.name == "FlashForge AD5X"


@pytest.mark.asyncio
async def test_get_info_success_5m_pro():
    """get() parses 5M Pro details."""
    info = _build_info()
    detail_response = DetailResponse(**FIVE_M_PRO_INFO_RESPONSE)
    info.get_detail_response = AsyncMock(return_value=detail_response)

    machine_info = await info.get()

    assert machine_info is not None
    assert machine_info.is_ad5x is False
    assert machine_info.is_pro is True


@pytest.mark.asyncio
async def test_get_info_accepts_extended_ad5x_detail_fields():
    """AD5X detail parsing should tolerate newer firmware capability fields."""
    info = _build_info()
    payload = json.loads(json.dumps(AD5X_INFO_RESPONSE))
    payload["detail"].update(
        {
            "camera": 1,
            "clearFanStatus": "open",
            "coordinate": [10000.0, 10000.0, 10000.0],
            "extrudeCtrl": 1,
            "moveCtrl": 1,
            "unexpectedFutureField": {"value": 1},
        }
    )
    detail_response = DetailResponse(**payload)
    info.get_detail_response = AsyncMock(return_value=detail_response)

    machine_info = await info.get()

    assert machine_info is not None
    assert machine_info.is_ad5x is True


@pytest.mark.asyncio
async def test_is_printing_true():
    """is_printing returns True when status printing."""
    info = _build_info()
    info.get = AsyncMock(return_value=FFMachineInfo(status="printing"))

    assert await info.is_printing() is True
    info.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_machine_state_ready():
    """get_machine_state returns MachineState when available."""
    info = _build_info()
    machine_info = FFMachineInfo(machine_state=MachineState.READY)
    info.get = AsyncMock(return_value=machine_info)

    state = await info.get_machine_state()

    assert state == MachineState.READY


@pytest.mark.asyncio
async def test_get_detail_response_http_error():
    """HTTP errors return None without raising."""
    info = _build_info()
    mock_session = _mock_session({}, status=500)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        detail = await info.get_detail_response()

    assert detail is None


# ---------------------------------------------------------------------------
# Transport failure vs. content failure
#
# These two must not look alike to callers. A None return means we never got an
# answer - check the network. A FlashForgeResponseError means the printer
# answered with something we could not read - that is a bug to report. Issue #18
# spent three releases blaming the network for a schema problem because both
# paths returned None.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unparseable_payload_raises_rather_than_returning_none():
    """A body that fails validation is a response error, not an absent printer."""
    info = _build_info()
    # `detail` is required on DetailResponse, so omitting it fails validation
    # for a reason that has nothing to do with connectivity.
    mock_session = _mock_session({"code": 0})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(FlashForgeResponseError) as excinfo:
            await info.get_detail_response()

    assert Endpoints.DETAIL in str(excinfo.value)


@pytest.mark.asyncio
async def test_non_object_body_raises():
    """A JSON body that is not an object cannot be a /detail response."""
    info = _build_info()
    mock_session = _mock_session(["not", "an", "object"])

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(FlashForgeResponseError):
            await info.get_detail_raw()


@pytest.mark.asyncio
async def test_get_detail_raw_skips_validation_entirely():
    """The raw accessor hands back identity fields even from a payload we could
    not validate - this is what lets the config flow read `pid` first."""
    info = _build_info()
    mock_session = _mock_session({"code": 0, "detail": {"pid": 40, "chamberTemp": -108}})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        raw = await info.get_detail_raw()

    assert raw["detail"]["pid"] == 40


@pytest.mark.asyncio
async def test_get_raises_when_conversion_fails():
    """A payload we validated but could not convert is still a response error."""
    info = _build_info()
    detail_response = DetailResponse(**FIVE_M_PRO_INFO_RESPONSE)
    info.get_detail_response = AsyncMock(return_value=detail_response)

    with patch.object(MachineInfoParser, "from_detail", return_value=None):
        with pytest.raises(FlashForgeResponseError):
            await info.get()


@pytest.mark.asyncio
async def test_get_returns_none_when_printer_unreachable():
    """An unreachable printer is still a plain None - callers rely on that."""
    info = _build_info()
    info.get_detail_response = AsyncMock(return_value=None)

    assert await info.get() is None


@pytest.mark.asyncio
async def test_convenience_wrappers_absorb_response_errors():
    """is_printing/get_status/get_machine_state keep their documented fallbacks."""
    info = _build_info()
    info.get = AsyncMock(side_effect=FlashForgeResponseError("bad payload"))

    assert await info.is_printing() is False
    assert await info.get_status() is None
    assert await info.get_machine_state() is None


# --------------------------------------------------------------------------- #
# Status mapping
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("reported", "expected"),
    [
        ("ready", MachineState.READY),
        ("printing", MachineState.PRINTING),
        ("pausing", MachineState.PAUSING),
        ("paused", MachineState.PAUSED),
        # A Creator 5 Pro reports "pause", not the documented "paused".
        ("pause", MachineState.PAUSED),
        ("PAUSE", MachineState.PAUSED),
        # Sent while a file is being transferred to the printer.
        ("downloading", MachineState.BUSY),
        ("completed", MachineState.COMPLETED),
    ],
)
def test_machine_state_mapping(reported, expected):
    """Every status a real printer has been seen to report must map."""
    assert MachineInfoParser._get_machine_state(reported) is expected


def test_unmapped_status_is_unknown_and_logged(caplog):
    """An unrecognized status still degrades to UNKNOWN - and says so.

    The warning is the only trace an unmapped value leaves: the state itself
    becomes UNKNOWN, which is indistinguishable from a printer that reported
    nothing. Both "pause" and "downloading" were found this way, in a Home
    Assistant log, after the sensor had been reading "unknown" for a day.
    """
    with caplog.at_level("WARNING"):
        assert MachineInfoParser._get_machine_state("teleporting") is MachineState.UNKNOWN

    assert "teleporting" in caplog.text


def test_empty_status_is_unknown_without_a_warning():
    """No status is not an unexpected status; it must not cry wolf."""
    assert MachineInfoParser._get_machine_state("") is MachineState.UNKNOWN
    assert MachineInfoParser._get_machine_state(None) is MachineState.UNKNOWN
