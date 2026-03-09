"""
G-code controller for FlashForge Adventurer 3 printers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .gcode_controller import GCodeController

if TYPE_CHECKING:
    from ..a3_client import A3FileEntry, A3PrinterInfo, A3Thumbnail, FlashForgeA3Client
    from ..parsers import EndstopStatus, LocationInfo, PrintStatus


class A3GCodeController(GCodeController):
    """High-level G-code controller for Adventurer 3 printers."""

    client: FlashForgeA3Client

    def __init__(self, client: FlashForgeA3Client) -> None:
        super().__init__(client)
        self.client = client

    async def set_printer_name(self, name: str) -> bool:
        return await self.client.set_printer_name(name)

    async def get_print_status(self) -> PrintStatus | None:
        return await self.client.get_print_status()

    async def list_files(self) -> list[A3FileEntry]:
        return await self.client.list_files()

    async def get_thumbnail(self, filename: str) -> A3Thumbnail | None:
        return await self.client.get_thumbnail(filename)

    async def select_file(self, filename: str) -> bool:
        return await self.client.select_file(filename)

    async def start_job(self, filename: str) -> bool:
        if not await self.client.select_file(filename):
            return False
        return await self.client.start_print()

    async def get_current_position(self) -> LocationInfo | None:
        return await self.client.get_position()

    async def get_endstop_status(self) -> EndstopStatus | None:
        return await self.client.get_endstop_status()

    async def enable_motors(self) -> bool:
        return await self.client.enable_motors()

    async def disable_motors(self) -> bool:
        return await self.client.disable_motors()

    async def emergency_stop(self) -> bool:
        return await self.client.emergency_stop()

    async def cancel_heat_wait(self) -> bool:
        return await self.client.cancel_heat_wait()

    async def led_control(self, params: str) -> bool:
        return await self.client.led_control(params)

    async def custom_m144(self, params: str | None = None) -> str | None:
        return await self.client.custom_m144(params)

    async def custom_m145(self, params: str | None = None) -> str | None:
        return await self.client.custom_m145(params)

    async def get_printer_model(self) -> str | None:
        info = await self.client.get_printer_info()
        return info.machine_type if info else None

    async def custom_m651(self) -> str | None:
        return await self.client.custom_m651()

    async def custom_m652(self) -> str | None:
        return await self.client.custom_m652()

    async def custom_m653(self, params: str) -> bool:
        return await self.client.custom_m653(params)

    async def custom_m654(self, params: str) -> bool:
        return await self.client.custom_m654(params)

    async def custom_m611(self) -> str | None:
        return await self.client.custom_m611()

    async def custom_m612(self) -> str | None:
        return await self.client.custom_m612()

    async def get_printer_info(self) -> A3PrinterInfo | None:
        return await self.client.get_printer_info()

    async def is_adventurer_3(self) -> bool:
        info = await self.get_printer_info()
        if not info:
            return False
        machine_type = info.machine_type.lower()
        return (
            "adventurer3" in machine_type
            or "adventurer 3" in machine_type
            or "adventurer iii" in machine_type
        )

    async def get_detailed_position(self) -> LocationInfo | None:
        return await self.client.get_position_xyze()
