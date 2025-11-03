"""
Unit tests for temperature control operations.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from flashforge.client import FlashForgeClient
from flashforge.api.controls.temp_control import TempControl
from flashforge.tcp.ff_client import FlashForgeClient as TcpFlashForgeClient


def _build_http_client() -> FlashForgeClient:
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.tcp_client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_set_extruder_temp_success():
    """Delegates extruder temperature setting to TCP client."""
    client = _build_http_client()
    client.tcp_client.set_extruder_temp.return_value = True
    temp_control = TempControl(client)

    result = await temp_control.set_extruder_temp(220, wait_for=True)

    assert result is True
    client.tcp_client.set_extruder_temp.assert_awaited_once_with(220, True)


@pytest.mark.asyncio
async def test_cancel_extruder_temp():
    """Cancels extruder temperature through TCP client."""
    client = _build_http_client()
    client.tcp_client.cancel_extruder_temp.return_value = True
    temp_control = TempControl(client)

    assert await temp_control.cancel_extruder_temp() is True
    client.tcp_client.cancel_extruder_temp.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_bed_temp_success():
    """Delegates bed temperature setting."""
    client = _build_http_client()
    client.tcp_client.set_bed_temp.return_value = True
    temp_control = TempControl(client)

    result = await temp_control.set_bed_temp(60, wait_for=False)

    assert result is True
    client.tcp_client.set_bed_temp.assert_awaited_once_with(60, False)


@pytest.mark.asyncio
async def test_wait_for_part_cool_threshold():
    """High-level TCP client waits until components cool below threshold."""
    client = TcpFlashForgeClient("192.168.1.120")
    client.cancel_extruder_temp = AsyncMock(return_value=True)
    client.cancel_bed_temp = AsyncMock(return_value=True)

    class FakeTemp:
        def __init__(self, current):
            self._current = current

        def get_current(self):
            return self._current

        def get_set(self):
            return 0

    class TempSequence:
        def __init__(self):
            self.steps = [
                (70, 70),
                (55, 55),
                (45, 45),
            ]

        def __call__(self):
            if self.steps:
                extruder, bed = self.steps.pop(0)
            else:
                extruder = bed = 40

            return SimpleNamespace(
                get_extruder_temp=lambda: FakeTemp(extruder),
                get_bed_temp=lambda: FakeTemp(bed),
            )

    sequence = TempSequence()
    client.get_temp_info = AsyncMock(side_effect=lambda: sequence())

    with patch("flashforge.tcp.ff_client.asyncio.sleep", new=AsyncMock(return_value=None)):
        result = await client.wait_for_part_cool(target_temp=50, timeout_seconds=120)

    assert result is True
    assert client.get_temp_info.await_count >= 2


@pytest.mark.asyncio
async def test_set_temp_out_of_range():
    """Out-of-range values bubble up failure result from TCP layer."""
    client = _build_http_client()
    client.tcp_client.set_extruder_temp.return_value = False
    temp_control = TempControl(client)

    assert await temp_control.set_extruder_temp(999, wait_for=False) is False
