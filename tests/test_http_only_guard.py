"""
Unit tests for the HTTP-only (Creator 5 / 5 Pro) TCP guard.

Mirrors the TS FiveMClient gating: a printer with no TCP/8899 service must
no-op (return False + warn) on TCP-only operations instead of hanging on a
dead socket. HTTP-routed operations (temperature, configure_slot) are NOT
affected — they have HTTP equivalents.
"""

from unittest.mock import AsyncMock

import pytest

from flashforge.api.controls.control import Control
from flashforge.api.controls.temp_control import TempControl
from flashforge.client import FlashForgeClient


def _build_http_only_client(*, is_creator5: bool = True) -> FlashForgeClient:
    """Build a client forced into HTTP-only mode with a (mocked) TCP client."""
    client = FlashForgeClient("192.168.1.150", "SN123", "CODE123")
    client._http_only = True  # noqa: SLF001 - test-only transport override
    client.is_creator5 = is_creator5
    client.is_creator5_pro = False
    client.tcp_client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_can_use_tcp_returns_false_when_http_only():
    """can_use_tcp is False for an HTTP-only client."""
    client = _build_http_only_client()

    assert client.can_use_tcp("home_axes") is False


@pytest.mark.asyncio
async def test_can_use_tcp_returns_true_for_dual_api_client():
    """can_use_tcp is True for a normal dual-API (HTTP+TCP) client."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client._http_only = False  # noqa: SLF001

    assert client.can_use_tcp("home_axes") is True


@pytest.mark.asyncio
async def test_home_axes_noops_on_http_only():
    """home_axes returns False on an HTTP-only client without touching TCP."""
    client = _build_http_only_client()
    control = Control(client)

    result = await control.home_axes()

    assert result is False
    client.tcp_client.home_axes.assert_not_called()


@pytest.mark.asyncio
async def test_home_axes_rapid_noops_on_http_only():
    """home_axes_rapid returns False on an HTTP-only client without touching TCP."""
    client = _build_http_only_client()
    control = Control(client)

    result = await control.home_axes_rapid()

    assert result is False
    client.tcp_client.rapid_home.assert_not_called()


@pytest.mark.asyncio
async def test_turn_runout_sensor_on_noops_on_http_only():
    """turn_runout_sensor_on returns False on an HTTP-only client."""
    client = _build_http_only_client()
    control = Control(client)

    result = await control.turn_runout_sensor_on()

    assert result is False
    client.tcp_client.turn_runout_sensor_on.assert_not_called()


@pytest.mark.asyncio
async def test_turn_runout_sensor_off_noops_on_http_only():
    """turn_runout_sensor_off returns False on an HTTP-only client."""
    client = _build_http_only_client()
    control = Control(client)

    result = await control.turn_runout_sensor_off()

    assert result is False
    client.tcp_client.turn_runout_sensor_off.assert_not_called()


@pytest.mark.asyncio
async def test_temp_control_still_works_on_http_only():
    """Temperature control routes over HTTP on an HTTP-only client (does NOT no-op)."""
    client = _build_http_only_client()
    client.control.send_control_command = AsyncMock(return_value=True)  # type: ignore[method-assign]
    temp_control = TempControl(client)

    result = await temp_control.set_bed_temp(60)

    assert result is True
    client.tcp_client.set_bed_temp.assert_not_called()
    client.control.send_control_command.assert_awaited_once()


@pytest.mark.asyncio
async def test_home_axes_delegates_to_tcp_for_dual_api_client():
    """home_axes still delegates to TCP for a normal dual-API client (regression guard)."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client._http_only = False  # noqa: SLF001
    client.tcp_client = AsyncMock()
    client.tcp_client.home_axes.return_value = True
    control = Control(client)

    result = await control.home_axes()

    assert result is True
    client.tcp_client.home_axes.assert_awaited_once()
