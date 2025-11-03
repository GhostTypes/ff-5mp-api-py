"""
Unit tests for the main FlashForgeClient class.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from flashforge.client import FlashForgeClient, MachineInfoParser
from flashforge.models import FFMachineInfo
from flashforge.models.responses import DetailResponse

from tests.fixtures.printer_responses import (
    AD5X_INFO_RESPONSE,
    FIVE_M_PRO_INFO_RESPONSE,
    PRODUCT_RESPONSE,
)


def _build_machine_info(payload: dict) -> FFMachineInfo:
    """Helper to convert a detail payload into FFMachineInfo."""
    detail_response = DetailResponse(**payload)
    machine_info = MachineInfoParser.from_detail(detail_response.detail)
    assert machine_info is not None  # Guard against malformed fixture
    return machine_info


@pytest.mark.asyncio
async def test_initialize_success():
    """Client initializes successfully with valid responses."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")

    detail_response = DetailResponse(**AD5X_INFO_RESPONSE)

    client.info.get_detail_response = AsyncMock(return_value=detail_response)
    client.tcp_client.get_printer_info = AsyncMock(
        return_value=SimpleNamespace(type_name="FlashForge AD5X")
    )

    with patch("flashforge.client.NetworkUtils.is_ok", return_value=True):
        result = await client.initialize()

    assert result is True
    client.info.get_detail_response.assert_awaited_once()
    client.tcp_client.get_printer_info.assert_awaited_once()
    assert client.printer_name == "FlashForge AD5X"
    assert client.is_ad5x is True
    assert client.firmware_version == "1.1.7-1.0.2"


@pytest.mark.asyncio
async def test_initialize_connection_failure():
    """Initialization fails gracefully when verify_connection returns False."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.verify_connection = AsyncMock(return_value=False)

    result = await client.initialize()

    assert result is False
    assert client.printer_name == ""


@pytest.mark.asyncio
async def test_verify_connection_http_api_fails():
    """verify_connection returns False when HTTP API fails."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.info.get_detail_response = AsyncMock(return_value=None)

    result = await client.verify_connection()

    assert result is False
    client.info.get_detail_response.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_connection_tcp_api_fails():
    """verify_connection handles TCP exception and returns False."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")

    detail_response = DetailResponse(**AD5X_INFO_RESPONSE)
    client.info.get_detail_response = AsyncMock(return_value=detail_response)
    client.tcp_client.get_printer_info = AsyncMock(side_effect=Exception("TCP failure"))

    with patch("flashforge.client.NetworkUtils.is_ok", return_value=True):
        result = await client.verify_connection()

    assert result is False
    client.info.get_detail_response.assert_awaited_once()
    client.tcp_client.get_printer_info.assert_awaited_once()


def test_cache_details_all_fields_ad5x():
    """cache_details populates AD5X-specific fields."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    machine_info = _build_machine_info(AD5X_INFO_RESPONSE)

    assert client.cache_details(machine_info) is True
    assert client.printer_name == "FlashForge AD5X"
    assert client.is_ad5x is True
    assert client.lifetime_filament_meters.endswith("m")
    assert client.firmware_version == "1.1.7-1.0.2"


def test_cache_details_all_fields_5m_pro():
    """cache_details populates 5M Pro fields and flags."""
    client = FlashForgeClient("192.168.1.140", "SN555", "CODE555")
    machine_info = _build_machine_info(FIVE_M_PRO_INFO_RESPONSE)

    assert client.cache_details(machine_info) is True
    assert client.printer_name == "Adventurer 5M Pro"
    assert client.is_ad5x is False
    assert client.is_pro is False  # cache_details does not change is_pro flag


@pytest.mark.asyncio
async def test_context_manager_lifecycle():
    """Async context manager initializes and disposes client."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client._ensure_http_session = AsyncMock()

    with patch.object(client, "initialize", AsyncMock(return_value=True)) as mock_init:
        with patch.object(client, "dispose", AsyncMock()) as mock_dispose:
            with pytest.raises(RuntimeError):
                async with client:
                    raise RuntimeError("boom")

    mock_init.assert_awaited_once()
    mock_dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_http_client_busy_state_management():
    """HTTP busy flag waits until released and release clears state."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client._http_client_busy = True

    async def release_later():
        await asyncio.sleep(0.01)
        client._http_client_busy = False

    asyncio.create_task(release_later())
    busy = await asyncio.wait_for(client.is_http_client_busy(), timeout=0.1)
    assert busy is False

    client._http_client_busy = True
    client.release_http_client()
    assert client._http_client_busy is False


@pytest.mark.asyncio
async def test_initialize_connection_timeout():
    """initialize handles timeout errors gracefully."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.info.get_detail_response = AsyncMock(side_effect=asyncio.TimeoutError)

    with patch("flashforge.client.NetworkUtils.is_ok", return_value=True):
        result = await client.initialize()

    assert result is False


@pytest.mark.asyncio
async def test_initialize_invalid_ip_address():
    """initialize handles invalid IP address errors."""
    client = FlashForgeClient("999.999.999.999", "SN123", "CODE123")
    client.info.get_detail_response = AsyncMock(side_effect=ValueError("Invalid IP"))

    result = await client.initialize()

    assert result is False


@pytest.mark.asyncio
async def test_initialize_network_unreachable():
    """initialize handles network unreachable errors."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.info.get_detail_response = AsyncMock(side_effect=OSError("Network unreachable"))

    result = await client.initialize()

    assert result is False
