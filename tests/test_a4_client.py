"""Parity tests for the Adventurer 4 TCP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from flashforge.tcp import A4FileEntry, FlashForgeA4Client


@pytest.mark.asyncio
async def test_a4_init_control_uses_documented_m601_s1_flow():
    """A4 init_control should use M601 S1 and then fetch M115 machine info."""
    client = FlashForgeA4Client("192.168.1.110")

    with (
        patch.object(
            client,
            "send_command_async",
            AsyncMock(
                side_effect=[
                    "CMD M601 Received.\nok\n",
                    "\n".join(
                        [
                            "CMD M115 Received.",
                            "Machine Type: Flashforge Adventurer 4",
                            "Machine Name: Shop Printer",
                            "Firmware: v2.0.5 20220527",
                            "X: 220 Y: 200 Z: 250",
                            "Tool Count: 1",
                            "Mac Address: 00:11:22:33:44:55",
                            "ok",
                        ]
                    ),
                ]
            ),
        ) as send_command,
        patch.object(client, "start_keep_alive", AsyncMock()),
    ):
        assert await client.init_control() is True
        assert send_command.call_args_list[0].args == ("~M601 S1",)
        assert send_command.call_args_list[1].args == ("~M115",)


@pytest.mark.asyncio
async def test_a4_init_control_accepts_already_connected():
    """M601 already-connected responses should still initialize successfully."""
    client = FlashForgeA4Client("192.168.1.110")

    with patch.object(
        client,
        "send_command_async",
        AsyncMock(return_value="Error: have been connected\n"),
    ):
        assert await client.init_control() is True


@pytest.mark.asyncio
async def test_a4_get_printer_info_parses_documented_lite_m115():
    """A4 Lite M115 parsing should follow the documented response format."""
    client = FlashForgeA4Client("192.168.1.110")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            return_value="\n".join(
                [
                    "CMD M115 Received.",
                    "Machine Type: Flashforge Adventurer 4",
                    "Machine Name: Lite Printer",
                    "Firmware: v2.0.5 20220527",
                    "X: 220 Y: 200 Z: 250",
                    "Tool Count: 1",
                    "Mac Address: 00:11:22:33:44:55",
                    "ok",
                ]
            )
        ),
    ):
        info = await client.get_printer_info()

    assert info is not None
    assert info.machine_type == "Flashforge Adventurer 4"
    assert info.machine_name == "Lite Printer"
    assert info.firmware == "v2.0.5 20220527"
    assert info.serial_number is None
    assert info.build_volume.x == 220
    assert info.build_volume.y == 200
    assert info.build_volume.z == 250
    assert info.variant == "lite"


@pytest.mark.asyncio
async def test_a4_get_printer_info_parses_documented_pro_m115():
    """A4 Pro M115 parsing should preserve the documented Pro machine type."""
    client = FlashForgeA4Client("192.168.1.110")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            return_value="\n".join(
                [
                    "CMD M115 Received.",
                    "Machine Type: Flashforge Adventurer 4 Pro",
                    "Machine Name: Pro Printer",
                    "Firmware: v1.2.1 20230906",
                    "X: 220 Y: 200 Z: 250",
                    "Tool Count: 1",
                    "Mac Address: 66:55:44:33:22:11",
                    "ok",
                ]
            )
        ),
    ):
        info = await client.get_printer_info()

    assert info is not None
    assert info.variant == "pro"
    assert info.firmware == "v1.2.1 20230906"


@pytest.mark.asyncio
async def test_a4_get_printer_info_accepts_sn_prefixed_serials():
    """A4 M115 parsing should accept SN-prefixed serial numbers."""
    client = FlashForgeA4Client("192.168.1.110")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            return_value="\n".join(
                [
                    "CMD M115 Received.",
                    "Machine Type: Flashforge Adventurer 4",
                    "Machine Name: Serial Printer",
                    "Firmware: v2.0.5 20220527",
                    "SN: A4SN67890",
                    "X: 220 Y: 200 Z: 250",
                    "Tool Count: 1",
                    "Mac Address: 00:11:22:33:44:55",
                    "ok",
                ]
            )
        ),
    ):
        info = await client.get_printer_info()

    assert info is not None
    assert info.serial_number == "A4SN67890"


@pytest.mark.asyncio
async def test_a4_get_temp_info_parses_documented_m105():
    """A4 temperature parsing should support the documented M105 reply."""
    client = FlashForgeA4Client("192.168.1.110")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(return_value="CMD M105 Received.\nT0:185/200 B:60/60\nok"),
    ):
        temp_info = await client.get_temp_info()

    assert temp_info is not None
    assert temp_info.get_extruder_temp() is not None
    assert temp_info.get_extruder_temp().get_current() == 185
    assert temp_info.get_bed_temp() is not None
    assert temp_info.get_bed_temp().get_set() == 60


@pytest.mark.asyncio
async def test_a4_get_print_status_parses_m27():
    """A4 print progress should parse SD byte progress correctly."""
    client = FlashForgeA4Client("192.168.1.110")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(return_value="CMD M27 Received.\nSD printing byte 45/100\nok"),
    ):
        status = await client.get_print_status()

    assert status is not None
    assert status.get_sd_progress() == "45/100"
    assert status.get_print_percent() == 45


@pytest.mark.asyncio
async def test_a4_list_files_normalizes_generic_file_entries():
    """A4 list_files should normalize generic legacy file paths into typed entries."""
    client = FlashForgeA4Client("192.168.1.110")
    with patch.object(
        client,
        "get_file_list_async",
        AsyncMock(return_value=["benchy.gcode", "[FLASH]/cube.gx"]),
    ):
        files = await client.list_files()

    assert files == [
        A4FileEntry(name="benchy.gcode", path="/data/benchy.gcode"),
        A4FileEntry(name="cube.gx", path="/data/[FLASH]/cube.gx"),
    ]
