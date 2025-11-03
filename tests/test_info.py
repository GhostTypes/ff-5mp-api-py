"""
Unit tests for the Info module.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flashforge.client import FlashForgeClient
from flashforge.api.controls.info import Info
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
