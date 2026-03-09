"""
Unit tests for the main FlashForgeClient class.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flashforge.client import (
    FiveMClientConnectionOptions,
    FlashForgeClient,
    MachineInfoParser,
)
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


def _mock_http_session(response_payload: dict, status: int = 200) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=response_payload)

    mock_post_ctx = MagicMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_post_ctx)
    return mock_session


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
    assert client.is_pro is True


def test_cache_details_stores_camera_stream_url():
    """cache_details stores the runtime camera stream URL reported by the printer."""
    client = FlashForgeClient("192.168.1.140", "SN555", "CODE555")
    payload = {
        **FIVE_M_PRO_INFO_RESPONSE,
        "detail": {
            **FIVE_M_PRO_INFO_RESPONSE["detail"],
            "cameraStreamUrl": "http://192.168.1.140:8080/?action=stream",
        },
    }
    machine_info = _build_machine_info(payload)

    assert client.cache_details(machine_info) is True
    assert client.camera_stream_url == "http://192.168.1.140:8080/?action=stream"


def test_constructor_supports_connection_overrides():
    """Constructor applies HTTP/TCP overrides and optional LED availability override."""
    client = FlashForgeClient(
        "192.168.1.10",
        "SN-1",
        "CHK-1",
        options=FiveMClientConnectionOptions(
            http_port=19098,
            tcp_port=19099,
            led_control_override=True,
        ),
    )

    assert client.get_endpoint("/detail") == "http://192.168.1.10:19098/detail"
    assert client.tcp_client.port == 19099
    assert client.led_control is True


@pytest.mark.asyncio
async def test_send_product_command_stores_product_info_and_control_states():
    """send_product_command caches product info and detected feature flags."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client._ensure_http_session = AsyncMock(return_value=_mock_http_session(PRODUCT_RESPONSE))

    result = await client.send_product_command()

    assert result is True
    assert client.product_info is not None
    assert client.product_info.lightCtrlState == 1
    assert client.led_control is True
    assert client.filtration_control is True


@pytest.mark.asyncio
async def test_led_override_round_trip_restores_detected_product_state():
    """Manual LED override is additive and can be cleared back to detected product state."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    response_payload = {
        "code": 0,
        "product": {
            **PRODUCT_RESPONSE["product"],
            "lightCtrlState": 0,
        },
    }
    client._ensure_http_session = AsyncMock(return_value=_mock_http_session(response_payload))

    assert await client.send_product_command() is True
    assert client.led_control is False

    client.set_feature_overrides(led_control=True)
    assert client.led_control is True

    client.set_feature_overrides(led_control=None)
    assert client.led_control is False


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
