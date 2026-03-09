"""Parity tests for the Adventurer 3 TCP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from flashforge.tcp import A3GCodeController, FlashForgeA3Client


@pytest.mark.asyncio
async def test_a3_init_control_accepts_already_connected():
    """M601 already-connected responses should still initialize successfully."""
    client = FlashForgeA3Client("192.168.1.100")

    with patch.object(
        client,
        "send_command_async",
        AsyncMock(return_value="Error: have been connected\n"),
    ):
        assert await client.init_control() is True


@pytest.mark.asyncio
async def test_a3_get_printer_info_parses_documented_m115():
    """A3 M115 parsing should follow the documented response format."""
    client = FlashForgeA3Client("192.168.1.100")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            return_value="\n".join(
            [
                "echo: Machine Type: FlashForge Adventurer III",
                "Machine Name: MyPrinter",
                "Firmware: v1.3.7",
                "Serial Number: SNADVA3M12345",
                "X: 150 Y: 150 Z: 150",
                "Tool Count: 1",
                "Mac Address:00:11:22:33:44:55",
                "",
            ]
            )
        ),
    ):
        info = await client.get_printer_info()

    assert info is not None
    assert info.machine_type == "FlashForge Adventurer III"
    assert info.machine_name == "MyPrinter"
    assert info.firmware == "v1.3.7"
    assert info.serial_number == "SNADVA3M12345"
    assert info.build_volume.x == 150
    assert info.build_volume.y == 150
    assert info.build_volume.z == 150
    assert info.tool_count == 1
    assert info.mac_address == "00:11:22:33:44:55"


@pytest.mark.asyncio
async def test_a3_list_files_parses_documented_m661():
    """A3 file listings should parse size headers and file names."""
    client = FlashForgeA3Client("192.168.1.100")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            return_value="\n".join(
            [
                "CMD M661 Received.",
                "info_list.size: 3",
                "test1.gcode",
                "test2.gx",
                "test3.g",
            ]
            )
        ),
    ):
        files = await client.list_files()

    assert len(files) == 3
    assert files[0].name == "test1.gcode"
    assert files[0].path == "/data/test1.gcode"


@pytest.mark.asyncio
async def test_a3_get_thumbnail_parses_binary_magic_header():
    """A3 thumbnail parsing should honor the Adventurer 3 header format."""
    client = FlashForgeA3Client("192.168.1.100")
    payload = bytearray(100)
    payload[0:4] = b"\xA2\xA2\x2A\x2A"
    payload[4:8] = (92).to_bytes(4, byteorder="big")
    response = b"CMD M662 Received.\nack header length: 64\n" + bytes(payload)

    with patch.object(
        client,
        "send_command_async",
        AsyncMock(return_value=response.decode("latin1")),
    ):
        thumbnail = await client.get_thumbnail("test.gcode")

    assert thumbnail is not None
    assert len(thumbnail.data) == 92


@pytest.mark.asyncio
async def test_a3_print_status_uses_sd_progress_without_layers():
    """A3 print progress should fall back to SD byte progress."""
    client = FlashForgeA3Client("192.168.1.100")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(return_value='ack: "SD printing byte 45/100\r\n"'),
    ):
        status = await client.get_print_status()

    assert status is not None
    assert status.get_sd_progress() == "45/100"
    assert status.get_print_percent() == 45


@pytest.mark.asyncio
async def test_a3_get_temp_info_parses_single_line_m105():
    """A3 temperature parsing should support single-line M105 replies."""
    client = FlashForgeA3Client("192.168.1.100")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(return_value="ok T0:185/200 B:60/60\r\n"),
    ):
        temp_info = await client.get_temp_info()

    assert temp_info is not None
    assert temp_info.get_extruder_temp() is not None
    assert temp_info.get_extruder_temp().get_current() == 185
    assert temp_info.get_bed_temp() is not None
    assert temp_info.get_bed_temp().get_set() == 60


@pytest.mark.asyncio
async def test_a3_get_endstop_status_parses_documented_m119():
    """A3 endstop parsing should support the documented status fields."""
    client = FlashForgeA3Client("192.168.1.100")
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            return_value="\n".join(
            [
                "echo: Endstop: X-max: 0 Y-max: 0 Z-min: 1",
                "MachineStatus: IDLE",
                "MoveMode: 0.0",
                "FilamentStatus: ok",
                "LEDStatus: on",
                "PrintFileName: test.gcode",
            ]
            )
        ),
    ):
        endstop = await client.get_endstop_status()

    assert endstop is not None
    assert endstop.is_ready() is True
    assert endstop.endstop is not None
    assert endstop.endstop.z_min == 1
    assert endstop.filament_status == "ok"
    assert endstop.led_enabled is True
    assert endstop.current_file == "test.gcode"


@pytest.mark.asyncio
async def test_a3_controller_maps_led_commands_to_m146():
    """The shared controller LED methods should map to Adventurer 3 M146 semantics."""
    client = FlashForgeA3Client("192.168.1.100")
    controller = A3GCodeController(client)
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(side_effect=['ack: "M146 1"\n', 'ack: "M146 0"\n']),
    ) as send_command:
        assert await controller.led_on() is True
        assert await controller.led_off() is True
        assert send_command.call_args_list[0].args == ("~M146 1",)
        assert send_command.call_args_list[1].args == ("~M146 0",)


@pytest.mark.asyncio
async def test_a3_controller_start_job_selects_then_starts():
    """The A3 controller should follow the M23/M24 file selection flow."""
    client = FlashForgeA3Client("192.168.1.100")
    controller = A3GCodeController(client)
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            side_effect=[
                "File opened: /data/test.gcode Size: 123456\nDone printing file\nok\n",
                'ack: "M24"\n',
            ]
        ),
    ) as send_command:
        assert await controller.start_job("test.gcode") is True
        assert send_command.call_args_list[0].args == ("~M23 /data/test.gcode",)
        assert send_command.call_args_list[1].args == ("~M24",)


@pytest.mark.asyncio
async def test_a3_controller_get_printer_model_uses_m115():
    """The controller should derive the A3 model name from M115, not legacy M650 semantics."""
    client = FlashForgeA3Client("192.168.1.100")
    controller = A3GCodeController(client)
    with patch.object(
        client,
        "send_command_async",
        AsyncMock(
            return_value="\n".join(
            [
                "echo: Machine Type: FlashForge Adventurer III",
                "Machine Name: MyPrinter",
                "Firmware: v1.3.7",
                "Serial Number: SNADVA3M12345",
                "X: 150 Y: 150 Z: 150",
                "Tool Count: 1",
                "Mac Address:00:11:22:33:44:55",
                "",
            ]
            )
        ),
    ) as send_command:
        assert await controller.get_printer_model() == "FlashForge Adventurer III"
        send_command.assert_called_once_with("~M115")
