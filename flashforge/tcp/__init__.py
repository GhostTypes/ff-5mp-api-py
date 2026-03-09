"""
TCP communication layer for FlashForge 3D printers.

This module provides low-level TCP socket communication and high-level G-code interfaces
for controlling FlashForge printers via their TCP API.
"""

from .a3_client import A3BuildVolume, A3FileEntry, A3PrinterInfo, A3Thumbnail, FlashForgeA3Client
from .ff_client import FlashForgeClient
from .gcode import A3GCodeController, GCodeController, GCodes
from .parsers import (
    Endstop,
    EndstopStatus,
    LocationInfo,
    MachineStatus,
    MoveMode,
    PrinterInfo,
    PrintStatus,
    Status,
    TempData,
    TempInfo,
    ThumbnailInfo,
)
from .tcp_client import FlashForgeTcpClient, FlashForgeTcpClientOptions

__all__ = [
    "FlashForgeTcpClient",
    "FlashForgeTcpClientOptions",
    "FlashForgeClient",
    "FlashForgeA3Client",
    "GCodes",
    "GCodeController",
    "A3GCodeController",
    "A3BuildVolume",
    "A3PrinterInfo",
    "A3FileEntry",
    "A3Thumbnail",
    "PrinterInfo",
    "TempInfo",
    "TempData",
    "LocationInfo",
    "EndstopStatus",
    "MachineStatus",
    "MoveMode",
    "Status",
    "Endstop",
    "PrintStatus",
    "ThumbnailInfo",
]
