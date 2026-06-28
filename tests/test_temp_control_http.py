"""
Unit tests for HTTP-only temperature control (Creator 5 / 5 Pro).

Mirrors src/api/controls/TempControl.test.ts (HTTP-only mode + Creator 5
extruder temp sections). The Creator 5 / 5 Pro have no TCP channel, so
temperature control goes through the HTTP ``temperatureCtl_cmd`` instead of
G-code. These tests assert the exact wire payload, including the v1.6.1
nozzle-off ``0`` bugfix (the firmware ignores -100 inside the ``nozzles``
array).
"""

from unittest.mock import AsyncMock

import pytest

from flashforge.api.constants.commands import Commands
from flashforge.api.controls.temp_control import (
    NOZZLE_COUNT,
    NOZZLE_OFF,
    TEMP_NO_CHANGE,
    TEMP_OFF,
    TempControl,
)
from flashforge.client import FlashForgeClient


def _build_http_only_client(*, is_creator5: bool = False) -> FlashForgeClient:
    """Build a client that is forced into HTTP-only mode, with the control
    command mocked so the payload can be inspected."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client._http_only = True  # noqa: SLF001 - test-only transport override
    client.is_creator5 = is_creator5
    client.is_creator5_pro = False
    # Mock the TCP client so we can assert TCP methods are NOT called.
    client.tcp_client = AsyncMock()
    # Replace the real HTTP send with a mock so we can inspect the payload.
    client.control.send_control_command = AsyncMock(return_value=True)  # type: ignore[method-assign]
    return client


# ---------------------------------------------------------------------------
# HTTP-only mode (not Creator 5) -- the AD5X / 5M path forced into httpOnly.
# Keeps rightNozzle for the generic extruder commands.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_set_extruder_temp_http_only_uses_right_nozzle():
    """set_extruder_temp sends temperatureCtl_cmd with rightNozzle, leaving others -200."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    result = await temp_control.set_extruder_temp(215)

    assert result is True
    client.tcp_client.set_extruder_temp.assert_not_called()
    client.control.send_control_command.assert_awaited_once_with(
        Commands.TEMP_CONTROL_CMD,
        {"rightNozzle": 215, "leftNozzle": -200, "platform": -200, "chamber": -200},
    )


@pytest.mark.asyncio
async def test_set_bed_temp_http_only_uses_platform():
    """set_bed_temp sends temperatureCtl_cmd with platform set."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    await temp_control.set_bed_temp(60)

    client.tcp_client.set_bed_temp.assert_not_called()
    client.control.send_control_command.assert_awaited_once_with(
        Commands.TEMP_CONTROL_CMD,
        {"rightNozzle": -200, "leftNozzle": -200, "platform": 60, "chamber": -200},
    )


@pytest.mark.asyncio
async def test_cancel_extruder_temp_http_only_turns_right_nozzle_off():
    """cancel_extruder_temp turns the right nozzle off (-100)."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    await temp_control.cancel_extruder_temp()

    client.tcp_client.cancel_extruder_temp.assert_not_called()
    payload = client.control.send_control_command.await_args.args[1]
    assert payload["rightNozzle"] == TEMP_OFF
    assert payload["platform"] == TEMP_NO_CHANGE


@pytest.mark.asyncio
async def test_cancel_bed_temp_http_only_turns_platform_off():
    """cancel_bed_temp turns the platform off (-100)."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    await temp_control.cancel_bed_temp()

    client.tcp_client.cancel_bed_temp.assert_not_called()
    payload = client.control.send_control_command.await_args.args[1]
    assert payload["platform"] == TEMP_OFF
    assert payload["rightNozzle"] == TEMP_NO_CHANGE


@pytest.mark.asyncio
async def test_wait_for_part_cool_is_noop_http_only():
    """wait_for_part_cool is a no-op (no TCP polling) on HTTP-only printers."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    result = await temp_control.wait_for_part_cool(40)

    assert result is False
    client.tcp_client.wait_for_part_cool.assert_not_called()


@pytest.mark.asyncio
async def test_set_tool_temp_sets_one_tool_leaves_others_unchanged():
    """set_tool_temp sets one tool and leaves the others at -200."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    result = await temp_control.set_tool_temp(2, 230)

    assert result is True
    payload = client.control.send_control_command.await_args.args[1]
    assert payload["nozzles"] == [-200, -200, 230, -200]


@pytest.mark.asyncio
async def test_set_tool_temps_sends_all_four_targets():
    """set_tool_temps sends all four per-tool targets."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    await temp_control.set_tool_temps([200, 210, 220, 230])

    payload = client.control.send_control_command.await_args.args[1]
    assert payload["nozzles"] == [200, 210, 220, 230]


@pytest.mark.asyncio
async def test_cancel_tool_temp_uses_zero_not_minus_100():
    """cancel_tool_temp turns a single tool off via 0 (firmware ignores -100 in nozzles[])."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    await temp_control.cancel_tool_temp(0)

    payload = client.control.send_control_command.await_args.args[1]
    assert payload["nozzles"] == [0, -200, -200, -200]


@pytest.mark.asyncio
async def test_set_chamber_temp_http_only():
    """set_chamber_temp sends temperatureCtl_cmd with the chamber set."""
    client = _build_http_only_client(is_creator5=True)
    temp_control = TempControl(client)

    result = await temp_control.set_chamber_temp(50)

    assert result is True
    payload = client.control.send_control_command.await_args.args[1]
    assert payload["chamber"] == 50
    assert payload["rightNozzle"] == TEMP_NO_CHANGE
    assert payload["platform"] == TEMP_NO_CHANGE


@pytest.mark.asyncio
async def test_cancel_chamber_temp_http_only():
    """cancel_chamber_temp turns the chamber off (-100)."""
    client = _build_http_only_client(is_creator5=True)
    temp_control = TempControl(client)

    await temp_control.cancel_chamber_temp()

    payload = client.control.send_control_command.await_args.args[1]
    assert payload["chamber"] == TEMP_OFF


@pytest.mark.asyncio
async def test_set_chamber_temp_refused_on_non_creator5():
    """set_chamber_temp is model-gated to the Creator 5 series."""
    client = _build_http_only_client()  # is_creator5 = False
    temp_control = TempControl(client)

    result = await temp_control.set_chamber_temp(50)

    assert result is False
    client.control.send_control_command.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_tool_temp_rejects_out_of_range_index():
    """set_tool_temp rejects an out-of-range index without sending."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    result = await temp_control.set_tool_temp(5, 200)

    assert result is False
    client.control.send_control_command.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_tool_temps_rejects_wrong_length():
    """set_tool_temps rejects a wrong-length array without sending."""
    client = _build_http_only_client()
    temp_control = TempControl(client)

    result = await temp_control.set_tool_temps([200, 210])

    assert result is False
    client.control.send_control_command.assert_not_awaited()


# ---------------------------------------------------------------------------
# Creator 5 (isCreator5) drives its tools ONLY via the `nozzles` array; the
# firmware's doTemperatureControl handler never reads rightNozzle/leftNozzle.
# The generic set/cancel_extruder_temp must therefore emit a 4-element
# `nozzles` array targeting the primary tool (T0).
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_creator5_set_extruder_temp_drives_t0_via_nozzles():
    """C5 set_extruder_temp drives T0 via nozzles[] and does NOT send rightNozzle target."""
    client = _build_http_only_client(is_creator5=True)
    temp_control = TempControl(client)

    result = await temp_control.set_extruder_temp(215)

    assert result is True
    client.tcp_client.set_extruder_temp.assert_not_called()
    client.control.send_control_command.assert_awaited_once_with(
        Commands.TEMP_CONTROL_CMD,
        {
            "rightNozzle": TEMP_NO_CHANGE,  # not set
            "leftNozzle": TEMP_NO_CHANGE,
            "platform": TEMP_NO_CHANGE,
            "chamber": TEMP_NO_CHANGE,
            "nozzles": [215, -200, -200, -200],
        },
    )


@pytest.mark.asyncio
async def test_creator5_cancel_extruder_temp_turns_t0_off_via_nozzles():
    """C5 cancel_extruder_temp turns T0 off via nozzles[] and does NOT send rightNozzle target."""
    client = _build_http_only_client(is_creator5=True)
    temp_control = TempControl(client)

    result = await temp_control.cancel_extruder_temp()

    assert result is True
    client.tcp_client.cancel_extruder_temp.assert_not_called()
    client.control.send_control_command.assert_awaited_once_with(
        Commands.TEMP_CONTROL_CMD,
        {
            "rightNozzle": TEMP_NO_CHANGE,  # not set
            "leftNozzle": TEMP_NO_CHANGE,
            "platform": TEMP_NO_CHANGE,
            "chamber": TEMP_NO_CHANGE,
            "nozzles": [0, -200, -200, -200],  # NOZZLE_OFF
        },
    )


@pytest.mark.asyncio
async def test_creator5_set_bed_temp_includes_4_entry_nozzles_array():
    """C5 set_bed_temp still includes a 4-entry nozzles[] array (all unchanged)."""
    client = _build_http_only_client(is_creator5=True)
    temp_control = TempControl(client)

    result = await temp_control.set_bed_temp(60)

    assert result is True
    client.tcp_client.set_bed_temp.assert_not_called()
    client.control.send_control_command.assert_awaited_once_with(
        Commands.TEMP_CONTROL_CMD,
        {
            "rightNozzle": TEMP_NO_CHANGE,
            "leftNozzle": TEMP_NO_CHANGE,
            "platform": 60,
            "chamber": TEMP_NO_CHANGE,
            "nozzles": [-200, -200, -200, -200],
        },
    )


@pytest.mark.asyncio
async def test_creator5_set_chamber_temp_includes_4_entry_nozzles_array():
    """C5 set_chamber_temp still includes a 4-entry nozzles[] array (all unchanged)."""
    client = _build_http_only_client(is_creator5=True)
    temp_control = TempControl(client)

    result = await temp_control.set_chamber_temp(50)

    assert result is True
    client.control.send_control_command.assert_awaited_once_with(
        Commands.TEMP_CONTROL_CMD,
        {
            "rightNozzle": TEMP_NO_CHANGE,
            "leftNozzle": TEMP_NO_CHANGE,
            "platform": TEMP_NO_CHANGE,
            "chamber": 50,
            "nozzles": [-200, -200, -200, -200],
        },
    )


# ---------------------------------------------------------------------------
# Constants sanity.
# ---------------------------------------------------------------------------
def test_constants_match_firmware_contract():
    """Temperature control sentinels match the firmware contract (v1.6.1)."""
    assert TEMP_NO_CHANGE == -200
    assert TEMP_OFF == -100
    assert NOZZLE_OFF == 0  # the v1.6.1 bugfix value
    assert NOZZLE_COUNT == 4
