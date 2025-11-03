"""
Unit tests for control operations.
"""
from unittest.mock import AsyncMock

import pytest

from flashforge.client import FlashForgeClient
from flashforge.api.controls.control import Commands, Control
from flashforge.models import FFMachineInfo


def _build_client() -> FlashForgeClient:
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.tcp_client = AsyncMock()
    client.info.get = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_set_led_on_with_led_control_enabled():
    """set_led_on sends light control command when LEDs available."""
    client = _build_client()
    client.led_control = True
    control = Control(client)
    control.send_control_command = AsyncMock(return_value=True)

    result = await control.set_led_on()

    assert result is True
    control.send_control_command.assert_awaited_once_with(
        Commands.LIGHT_CONTROL_CMD, {"status": "open"}
    )


@pytest.mark.asyncio
async def test_set_led_off():
    """set_led_off sends close payload."""
    client = _build_client()
    client.led_control = True
    control = Control(client)
    control.send_control_command = AsyncMock(return_value=True)

    result = await control.set_led_off()

    assert result is True
    control.send_control_command.assert_awaited_once_with(
        Commands.LIGHT_CONTROL_CMD, {"status": "close"}
    )


@pytest.mark.asyncio
async def test_set_external_filtration_on():
    """set_external_filtration_on issues filtration command."""
    client = _build_client()
    client.filtration_control = True
    control = Control(client)
    control._send_filtration_command = AsyncMock(return_value=True)

    result = await control.set_external_filtration_on()

    assert result is True
    args = control._send_filtration_command.call_args.args[0]
    assert args.internal == "close"
    assert args.external == "open"


@pytest.mark.asyncio
async def test_set_filtration_off():
    """set_filtration_off closes both fans."""
    client = _build_client()
    client.filtration_control = True
    control = Control(client)
    control._send_filtration_command = AsyncMock(return_value=True)

    result = await control.set_filtration_off()

    assert result is True
    args = control._send_filtration_command.call_args.args[0]
    assert args.internal == "close"
    assert args.external == "close"


@pytest.mark.asyncio
async def test_set_cooling_fan_speed_normal():
    """Cooling fan command respects requested speed during later layers."""
    client = _build_client()
    info = FFMachineInfo(status="printing", current_print_layer=5)
    client.info.get.return_value = info

    control = Control(client)
    control.send_control_command = AsyncMock(return_value=True)

    result = await control.set_cooling_fan_speed(80)

    assert result is True
    payload = control.send_control_command.await_args.args[1]
    assert payload["coolingFan"] == 80
    assert payload["chamberFan"] == 100  # Default unless clamped


@pytest.mark.asyncio
async def test_set_cooling_fan_speed_early_layer_protection():
    """Cooling fan speed clamped during first layers for safety."""
    client = _build_client()
    info = FFMachineInfo(status="printing", current_print_layer=1)
    client.info.get.return_value = info

    control = Control(client)
    control.send_control_command = AsyncMock(return_value=True)

    result = await control.set_cooling_fan_speed(90)

    assert result is True
    payload = control.send_control_command.await_args.args[1]
    assert payload["coolingFan"] == 0
    assert payload["chamberFan"] == 0


@pytest.mark.asyncio
async def test_home_axes_all():
    """home_axes delegates to tcp_client.home_axes."""
    client = _build_client()
    client.tcp_client.home_axes = AsyncMock(return_value=True)
    control = Control(client)

    assert await control.home_axes() is True
    client.tcp_client.home_axes.assert_awaited_once()
