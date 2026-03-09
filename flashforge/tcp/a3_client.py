"""
Adventurer 3 TCP client and typed helpers.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .parsers import EndstopStatus, LocationInfo, PrintStatus, TempInfo
from .tcp_client import FlashForgeTcpClient, FlashForgeTcpClientOptions

if TYPE_CHECKING:
    from .gcode import A3GCodeController


@dataclass(slots=True)
class A3BuildVolume:
    """Build volume metadata reported by Adventurer 3 M115 replies."""

    x: int
    y: int
    z: int


@dataclass(slots=True)
class A3PrinterInfo:
    """Structured Adventurer 3 printer info parsed from M115."""

    machine_type: str
    machine_name: str
    firmware: str
    serial_number: str
    build_volume: A3BuildVolume
    tool_count: int
    mac_address: str
    raw: str


@dataclass(slots=True)
class A3FileEntry:
    """File entry returned by the documented Adventurer 3 M661 response format."""

    name: str
    path: str
    size: int | None = None


@dataclass(slots=True)
class A3Thumbnail:
    """Thumbnail payload returned by Adventurer 3 M662."""

    data: bytes
    width: int | None = None
    height: int | None = None


class FlashForgeA3Client(FlashForgeTcpClient):
    """TCP client for FlashForge Adventurer 3 printers."""

    def __init__(self, hostname: str, options: FlashForgeTcpClientOptions | None = None) -> None:
        super().__init__(hostname, options)
        self._control: A3GCodeController | None = None

    def gcode(self) -> A3GCodeController:
        """Return the Adventurer 3 G-code controller."""
        if self._control is None:
            from .gcode import A3GCodeController

            self._control = A3GCodeController(self)
        return self._control

    def should_skip_response_wait(self, cmd: str) -> bool:
        bare_cmd = self._strip_protocol_prefix(cmd)
        return bool(re.match(r"^(G1|G28|G90|G91|G92)\b", bare_cmd))

    def should_use_inactivity_completion(self, cmd: str) -> bool:
        return not self.is_binary_command(cmd) and not self.should_skip_response_wait(cmd)

    def get_inactivity_completion_delay_ms(self, cmd: str) -> int:
        bare_cmd = self._strip_protocol_prefix(cmd)
        if bare_cmd.startswith("M661"):
            return 500
        if bare_cmd.startswith("M115") or bare_cmd.startswith("M119") or bare_cmd.startswith("M650"):
            return 250
        return 200

    def get_response_completion_delay_ms(self, cmd: str, binary: bool) -> int:
        if binary and self._strip_protocol_prefix(cmd).startswith("M662"):
            return 0
        return super().get_response_completion_delay_ms(cmd, binary)

    def is_binary_response_complete(self, cmd: str, response: bytearray) -> bool:
        if not self._strip_protocol_prefix(cmd).startswith("M662"):
            return super().is_binary_response_complete(cmd, response)

        buffer = bytes(response)
        text_prefix = buffer.decode("utf-8", errors="ignore")
        if "Error: File not exists" in text_prefix:
            return True

        magic_offset = buffer.find(b"\xA2\xA2\x2A\x2A")
        if magic_offset == -1 or len(buffer) < magic_offset + 8:
            return False

        length = int.from_bytes(buffer[magic_offset + 4 : magic_offset + 8], byteorder="big")
        return len(buffer) >= magic_offset + 8 + length

    def normalize_text_response(self, _cmd: str, response: str) -> str:
        return self._normalize_a3_text_response(response)

    async def init_control(self) -> bool:
        """Initialize control by sending M601."""
        try:
            await asyncio.sleep(0.5)
            response = await self.send_command_async("~M601")
            if response is None:
                return False
            if "Error: have been connected" in response:
                return True
            return self._is_successful_command_response("~M601", response)
        except Exception:
            return False

    async def get_printer_info(self) -> A3PrinterInfo | None:
        """Get printer information using the documented Adventurer 3 M115 response."""
        response = await self.send_command_async("~M115")
        if response is None:
            return None

        normalized = self._normalize_a3_text_response(response)
        lines = self._get_normalized_lines(normalized)
        info = A3PrinterInfo(
            machine_type="",
            machine_name="",
            firmware="",
            serial_number="",
            build_volume=A3BuildVolume(x=150, y=150, z=150),
            tool_count=1,
            mac_address="",
            raw=normalized,
        )

        for line in lines:
            if line.startswith("Machine Type:"):
                info.machine_type = line.replace("Machine Type:", "", 1).strip()
            elif line.startswith("Machine Name:"):
                info.machine_name = line.replace("Machine Name:", "", 1).strip()
            elif line.startswith("Firmware:"):
                info.firmware = line.replace("Firmware:", "", 1).strip()
            elif line.startswith("Serial Number:"):
                info.serial_number = line.replace("Serial Number:", "", 1).strip()
            elif line.startswith("Tool Count:"):
                try:
                    info.tool_count = int(line.replace("Tool Count:", "", 1).strip())
                except ValueError:
                    info.tool_count = 1
            elif line.startswith("Mac Address:"):
                info.mac_address = line.replace("Mac Address:", "", 1).strip()
            else:
                volume_match = re.search(r"X:\s*(\d+)\s+Y:\s*(\d+)\s+Z:\s*(\d+)", line, re.IGNORECASE)
                if volume_match:
                    info.build_volume = A3BuildVolume(
                        x=int(volume_match.group(1)),
                        y=int(volume_match.group(2)),
                        z=int(volume_match.group(3)),
                    )

        if not info.machine_type or not info.firmware:
            return None
        return info

    async def get_endstop_status(self) -> EndstopStatus | None:
        """Get the printer endstop and machine status using M119."""
        response = await self.send_command_async("~M119")
        if response is None:
            return None
        return EndstopStatus().from_replay(self._normalize_a3_text_response(response))

    async def set_printer_name(self, name: str) -> bool:
        """Set the printer name using M610."""
        return await self.send_cmd_ok(f"~M610 {name}")

    async def list_files(self) -> list[A3FileEntry]:
        """List files from printer storage using M661."""
        response = await self.send_command_async("~M661")
        if response is None:
            return []
        return self._parse_file_list(response)

    async def get_thumbnail(self, filename: str) -> A3Thumbnail | None:
        """Get a file thumbnail using M662."""
        response = await self.send_command_async(f"~M662 {filename}")
        if response is None:
            return None
        return self._parse_thumbnail(response)

    async def select_file(self, filename: str) -> bool:
        """Select a file for printing using M23."""
        resolved_path = filename if filename.startswith("/") else f"/data/{filename}"
        return await self.send_cmd_ok(f"~M23 {resolved_path}")

    async def start_print(self) -> bool:
        """Start the selected print job using M24."""
        return await self.send_cmd_ok("~M24")

    async def pause_print(self) -> bool:
        """Pause the active print job using M25."""
        return await self.send_cmd_ok("~M25")

    async def stop_print(self) -> bool:
        """Stop the active print job using M26."""
        return await self.send_cmd_ok("~M26")

    async def get_print_status(self) -> PrintStatus | None:
        """Get print progress using M27."""
        response = await self.send_command_async("~M27")
        if response is None:
            return None
        return PrintStatus().from_replay(self._normalize_a3_text_response(response))

    async def get_position(self) -> LocationInfo | None:
        """Get the current position using M114."""
        response = await self.send_command_async("~M114")
        if response is None:
            return None
        return LocationInfo().from_replay(self._normalize_a3_text_response(response))

    async def get_position_xyze(self) -> LocationInfo | None:
        """Get the detailed position using M663 when the firmware supports it."""
        response = await self.send_command_async("~M663")
        if response is None:
            return None
        return LocationInfo().from_replay(self._normalize_a3_text_response(response))

    async def home(self) -> bool:
        """Home all axes using G28."""
        return await self.send_cmd_ok("~G28")

    async def move(self, x: float, y: float, z: float, feedrate: int) -> bool:
        """Move the print head using G1."""
        return await self.send_cmd_ok(f"~G1 X{x} Y{y} Z{z} F{feedrate}")

    async def get_temp_info(self) -> TempInfo | None:
        """Get temperature information using M105."""
        response = await self.send_command_async("~M105")
        if response is None:
            return None
        return TempInfo().from_replay(self._normalize_a3_text_response(response))

    async def send_cmd_ok(self, cmd: str) -> bool:
        """Send a command and apply Adventurer 3 success semantics."""
        try:
            mapped_cmd = self._map_controller_command(cmd)
            response = await self.send_command_async(mapped_cmd)
            if response is None:
                return False
            if self.should_skip_response_wait(mapped_cmd):
                return True
            return self._is_successful_command_response(mapped_cmd, response)
        except Exception:
            return False

    async def enable_motors(self) -> bool:
        """Enable stepper motors using M17."""
        return await self.send_cmd_ok("~M17")

    async def disable_motors(self) -> bool:
        """Disable stepper motors using M18."""
        return await self.send_cmd_ok("~M18")

    async def emergency_stop(self) -> bool:
        """Perform an emergency stop using M112."""
        return await self.send_cmd_ok("~M112")

    async def cancel_heat_wait(self) -> bool:
        """Send M108. The Adventurer 3 firmware acknowledges it but treats it as a no-op."""
        return await self.send_cmd_ok("~M108")

    async def led_control(self, params: str) -> bool:
        """Control the accessory LED bar using M146."""
        return await self.send_cmd_ok(f"~M146 {params}")

    async def custom_m144(self, params: str | None = None) -> str | None:
        """Send M144 directly."""
        cmd = f"~M144 {params}" if params else "~M144"
        return await self.send_command_async(cmd)

    async def custom_m145(self, params: str | None = None) -> str | None:
        """Send M145 directly."""
        cmd = f"~M145 {params}" if params else "~M145"
        return await self.send_command_async(cmd)

    async def custom_m611(self) -> str | None:
        """Send M611 directly."""
        return await self.send_command_async("~M611")

    async def custom_m612(self) -> str | None:
        """Send M612 directly."""
        return await self.send_command_async("~M612")

    async def custom_m650(self) -> str | None:
        """Send M650 directly."""
        return await self.send_command_async("~M650")

    async def custom_m651(self) -> str | None:
        """Send M651 directly."""
        return await self.send_command_async("~M651")

    async def custom_m652(self) -> str | None:
        """Send M652 directly."""
        return await self.send_command_async("~M652")

    async def custom_m653(self, params: str) -> bool:
        """Send M653 with parameters."""
        return await self.send_cmd_ok(f"~M653 {params}")

    async def custom_m654(self, params: str) -> bool:
        """Send M654 with parameters."""
        return await self.send_cmd_ok(f"~M654 {params}")

    def _parse_file_list(self, response: str) -> list[A3FileEntry]:
        lines = self._get_normalized_lines(response)
        if any("CMD M661 Error." in line for line in lines):
            return []

        files: list[A3FileEntry] = []
        count_index = next(
            (index for index, line in enumerate(lines) if re.search(r"info_list\.size:\s*\d+", line)),
            -1,
        )
        if count_index == -1:
            return files

        count_match = re.search(r"info_list\.size:\s*(\d+)", lines[count_index], re.IGNORECASE)
        file_count = int(count_match.group(1)) if count_match else 0
        for line in lines[count_index + 1 :]:
            if len(files) >= file_count:
                break
            if not line or line == "ok" or line.startswith("CMD "):
                continue
            files.append(A3FileEntry(name=line, path=f"/data/{line}"))

        return files

    def _parse_thumbnail(self, response: str) -> A3Thumbnail | None:
        buffer = response.encode("latin1")
        error_text = buffer.decode("utf-8", errors="ignore")
        if "Error: File not exists" in error_text:
            return None

        magic_offset = buffer.find(b"\xA2\xA2\x2A\x2A")
        if magic_offset == -1 or len(buffer) < magic_offset + 8:
            return None

        payload_length = int.from_bytes(buffer[magic_offset + 4 : magic_offset + 8], byteorder="big")
        payload_end = magic_offset + 8 + payload_length
        if len(buffer) < payload_end:
            return None

        return A3Thumbnail(data=buffer[magic_offset + 8 : payload_end])

    def _normalize_a3_text_response(self, response: str) -> str:
        normalized = response.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        if lines:
            lines[0] = re.sub(r"^(ack|echo):\s*", "", lines[0], flags=re.IGNORECASE)
        normalized = "\n".join(lines).rstrip()

        if normalized.startswith('"') and normalized.endswith('"'):
            normalized = normalized[1:-1]

        return normalized.rstrip()

    def _get_normalized_lines(self, response: str) -> list[str]:
        return [line.strip() for line in self._normalize_a3_text_response(response).split("\n") if line.strip()]

    def _map_controller_command(self, cmd: str) -> str:
        if cmd == "~M146 r255 g255 b255 F0":
            return "~M146 1"
        if cmd == "~M146 r0 g0 b0 F0":
            return "~M146 0"
        return cmd

    def _is_successful_command_response(self, cmd: str, response: str) -> bool:
        normalized = self._normalize_a3_text_response(response).strip()
        if not normalized:
            return self.should_skip_response_wait(cmd)

        if "Error:" in normalized or "Control failed." in normalized:
            return False

        bare_cmd = self._strip_protocol_prefix(cmd)
        if bare_cmd.startswith("M23"):
            return "File opened" in normalized or "ok" in normalized
        if bare_cmd.startswith("M112"):
            return bool(re.search(r"Emergency Stop", normalized, re.IGNORECASE)) or "Received." in normalized
        if "ok" in normalized or "Received." in normalized:
            return True
        return normalized.startswith(bare_cmd)

    def _strip_protocol_prefix(self, cmd: str) -> str:
        return cmd.strip().removeprefix("~")
