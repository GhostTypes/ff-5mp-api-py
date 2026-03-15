"""
Adventurer 4 TCP client and typed helpers.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Literal

from .gcode import GCodeController, GCodes
from .parsers import EndstopStatus, LocationInfo, PrintStatus, TempInfo, ThumbnailInfo
from .tcp_client import FlashForgeTcpClient, FlashForgeTcpClientOptions

logger = logging.getLogger(__name__)

A4PrinterVariant = Literal["lite", "pro", "unknown"]


@dataclass(slots=True)
class A4BuildVolume:
    """Build volume metadata reported by Adventurer 4 M115 replies."""

    x: int
    y: int
    z: int


@dataclass(slots=True)
class A4PrinterInfo:
    """Structured Adventurer 4 printer info parsed from M115."""

    machine_type: str
    machine_name: str
    firmware: str
    serial_number: str | None
    build_volume: A4BuildVolume
    tool_count: int
    mac_address: str
    variant: A4PrinterVariant
    raw: str


@dataclass(slots=True)
class A4FileEntry:
    """Normalized file entry returned by the Adventurer 4 TCP client."""

    name: str
    path: str


class FlashForgeA4Client(FlashForgeTcpClient):
    """TCP client for FlashForge Adventurer 4 Lite and Pro printers."""

    def __init__(self, hostname: str, options: FlashForgeTcpClientOptions | None = None) -> None:
        super().__init__(hostname, options)
        self._control = GCodeController(self)

    def get_ip(self) -> str:
        """Return the configured printer hostname or IP address."""
        return self.hostname

    def gcode(self) -> GCodeController:
        """Return the shared G-code controller."""
        return self._control

    async def init_control(self) -> bool:
        """Initialize control using the documented M601 flow."""
        try:
            response = await self.send_command_async("~M601")
            if response is None:
                logger.error("A4: failed to send M601 connection command")
                return False

            if "Error: have been connected" in response:
                logger.warning("A4: already connected to printer")
                return True

            if not self._is_successful_command_response("~M601", response):
                return False

            await asyncio.sleep(0.1)
            info = await self.get_printer_info()
            if not info:
                logger.error("A4: failed to retrieve printer info after M601")
                return False

            await self.start_keep_alive()
            return True
        except Exception as error:
            logger.error("A4: init_control error: %s", error)
            return False

    async def led_on(self) -> bool:
        return await self._control.led_on()

    async def led_off(self) -> bool:
        return await self._control.led_off()

    async def pause_job(self) -> bool:
        return await self._control.pause_job()

    async def resume_job(self) -> bool:
        return await self._control.resume_job()

    async def stop_job(self) -> bool:
        return await self._control.stop_job()

    async def start_job(self, name: str) -> bool:
        return await self._control.start_job(name)

    async def home_axes(self) -> bool:
        return await self._control.home()

    async def rapid_home(self) -> bool:
        return await self._control.rapid_home()

    async def set_extruder_temp(self, temp: int, wait_for: bool = False) -> bool:
        return await self._control.set_extruder_temp(temp, wait_for)

    async def cancel_extruder_temp(self) -> bool:
        return await self._control.cancel_extruder_temp()

    async def set_bed_temp(self, temp: int, wait_for: bool = False) -> bool:
        return await self._control.set_bed_temp(temp, wait_for)

    async def cancel_bed_temp(self, wait_for_cool: bool = False) -> bool:
        return await self._control.cancel_bed_temp(wait_for_cool)

    async def extrude(self, length: float, feedrate: int = 450) -> bool:
        return await self.send_cmd_ok(f"~G1 E{length} F{feedrate}")

    async def move_extruder(self, x: float, y: float, feedrate: int) -> bool:
        return await self.send_cmd_ok(f"~G1 X{x} Y{y} F{feedrate}")

    async def move(self, x: float, y: float, z: float, feedrate: int) -> bool:
        return await self.send_cmd_ok(f"~G1 X{x} Y{y} Z{z} F{feedrate}")

    async def send_cmd_ok(self, cmd: str) -> bool:
        """Send a command and apply Adventurer 4 success semantics."""
        try:
            response = await self.send_command_async(cmd)
            if response is None:
                return False
            return self._is_successful_command_response(cmd, response)
        except Exception as error:
            logger.error("A4: send_cmd_ok failed for %s: %s", cmd, error)
            return False

    async def send_raw_cmd(self, cmd: str) -> str:
        """Send a raw command and return the raw string response."""
        if "M661" not in cmd:
            response = await self.send_command_async(cmd)
            return response or ""

        files = await self.get_file_list_async()
        return "\n".join(files)

    async def get_printer_info(self) -> A4PrinterInfo | None:
        """Get printer information using the documented Adventurer 4 M115 response."""
        response = await self.send_command_async(GCodes.CMD_INFO_STATUS)
        if response is None:
            return None

        normalized = self._normalize_a4_text_response(response)
        lines = self._get_normalized_lines(normalized)
        info = A4PrinterInfo(
            machine_type="",
            machine_name="",
            firmware="",
            serial_number=None,
            build_volume=A4BuildVolume(x=220, y=200, z=250),
            tool_count=1,
            mac_address="",
            variant="unknown",
            raw=normalized,
        )

        for line in lines:
            if line.startswith("Machine Type:"):
                info.machine_type = line.replace("Machine Type:", "", 1).strip()
                info.variant = self._detect_variant(info.machine_type)
            elif line.startswith("Machine Name:"):
                info.machine_name = line.replace("Machine Name:", "", 1).strip()
            elif line.startswith("Firmware:"):
                info.firmware = line.replace("Firmware:", "", 1).strip()
            elif line.startswith("SN:"):
                info.serial_number = line.replace("SN:", "", 1).strip()
            elif line.startswith("Serial Number:"):
                info.serial_number = line.replace("Serial Number:", "", 1).strip()
            elif line.startswith("Tool Count:") or line.startswith("Tool count:"):
                try:
                    info.tool_count = int(line.split(":", 1)[1].strip())
                except (IndexError, ValueError):
                    info.tool_count = 1
            elif line.startswith("Mac Address:"):
                info.mac_address = line.replace("Mac Address:", "", 1).strip()
            elif "X:" in line and "Y:" in line and "Z:" in line:
                volume_tokens = line.replace(":", "").split()
                try:
                    info.build_volume = A4BuildVolume(
                        x=int(volume_tokens[1]),
                        y=int(volume_tokens[3]),
                        z=int(volume_tokens[5]),
                    )
                except (IndexError, ValueError):
                    pass

        if not info.machine_type or not info.firmware:
            return None

        return info

    async def get_temp_info(self) -> TempInfo | None:
        response = await self.send_command_async(GCodes.CMD_TEMP)
        if response:
            return TempInfo().from_replay(self._normalize_a4_text_response(response))
        return None

    async def get_endstop_status(self) -> EndstopStatus | None:
        response = await self.send_command_async(GCodes.CMD_ENDSTOP_INFO)
        if response:
            return EndstopStatus().from_replay(self._normalize_a4_text_response(response))
        return None

    async def get_endstop_info(self) -> EndstopStatus | None:
        return await self.get_endstop_status()

    async def get_print_status(self) -> PrintStatus | None:
        response = await self.send_command_async(GCodes.CMD_PRINT_STATUS)
        if response:
            return PrintStatus().from_replay(self._normalize_a4_text_response(response))
        return None

    async def get_location_info(self) -> LocationInfo | None:
        response = await self.send_command_async(GCodes.CMD_INFO_XYZAB)
        if response:
            return LocationInfo().from_replay(self._normalize_a4_text_response(response))
        return None

    async def list_files(self) -> list[A4FileEntry]:
        files = await self.get_file_list_async()
        entries: list[A4FileEntry] = []
        for relative_path in files:
            normalized_path = (
                relative_path if relative_path.startswith("/data/") else f"/data/{relative_path}"
            )
            entries.append(
                A4FileEntry(
                    name=normalized_path.split("/")[-1] or relative_path,
                    path=normalized_path,
                )
            )
        return entries

    async def get_thumbnail(self, file_name: str) -> ThumbnailInfo | None:
        file_path = file_name if file_name.startswith("/data/") else f"/data/{file_name}"
        response = await self.send_command_async(f"{GCodes.CMD_GET_THUMBNAIL} {file_path}")
        if response:
            return ThumbnailInfo().from_replay(response, file_name)
        return None

    def _normalize_a4_text_response(self, response: str) -> str:
        normalized = response.replace("\r\n", "\n").replace("\r", "\n").rstrip()
        lines = normalized.split("\n")
        if lines:
            lines[0] = lines[0].removeprefix("ack: ").removeprefix("echo: ")
        normalized = "\n".join(lines).rstrip()

        if normalized.startswith('"') and normalized.endswith('"'):
            normalized = normalized[1:-1].rstrip()

        return normalized

    def _get_normalized_lines(self, response: str) -> list[str]:
        return [line.strip() for line in self._normalize_a4_text_response(response).split("\n") if line.strip()]

    def _detect_variant(self, machine_type: str) -> A4PrinterVariant:
        normalized_type = machine_type.upper()
        if "PRO" in normalized_type:
            return "pro"
        if "ADVENTURER 4" in normalized_type or "ADVENTURER4" in normalized_type:
            return "lite"
        return "unknown"

    def _is_successful_command_response(self, cmd: str, response: str) -> bool:
        normalized = self._normalize_a4_text_response(response).strip()
        if not normalized:
            return False

        lowered = normalized.lower()
        if "error:" in lowered or "control failed." in lowered:
            return False

        bare_cmd = cmd.strip().removeprefix("~").split(maxsplit=1)[0]
        if bare_cmd == "M23":
            return "File opened" in normalized or "ok" in lowered

        return "ok" in lowered or "Received." in normalized or normalized.startswith(bare_cmd)
