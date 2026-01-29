"""
FlashForge Python API

A Python library for controlling FlashForge 3D printers via HTTP and TCP APIs.
Provides comprehensive async support for printer control, job management, file operations,
temperature control, and real-time communication.

Example:
    Basic usage example:

    ```python
    import asyncio
    from flashforge import FlashForgeClient

    async def main():
        async with FlashForgeClient("192.168.1.100", "serial123", "check456") as client:
            if await client.initialize():
                print(f"Connected to {client.printer_name}")

                # Get printer status
                status = await client.get_printer_status()
                print(f"Status: {status.machine_state}")

                # Control operations
                await client.control.set_led_on()
                await client.control.home_axes()

                # Temperature monitoring
                temps = await client.get_temperatures()
                print(f"Extruder: {temps.extruder_temp}°C")

    asyncio.run(main())
    ```
"""

from .api.constants.commands import Commands
from .api.constants.endpoints import Endpoints

# Import control classes for advanced usage
from .api.controls import (
    Control,
    Files,
    Info,
    JobControl,
    TempControl,
)
from .api.filament import Filament
from .api.misc import Temperature as TempWrapper
from .api.misc import format_scientific_notation
from .api.network.fnet_code import FNetCode

# Import utility classes
from .api.network.utils import NetworkUtils
from .client import FlashForgeClient

# Import discovery classes
from .discovery import (
    FlashForgePrinter,
    FlashForgePrinterDiscovery,
)

# Import key models for convenience
from .models import (
    AD5XLocalJobParams,
    AD5XMaterialMapping,
    AD5XSingleColorJobParams,
    AD5XUploadParams,
    DetailResponse,
    FFGcodeFileEntry,
    FFGcodeToolData,
    FFMachineInfo,
    FFPrinterDetail,
    FilamentArgs,
    GCodeListResponse,
    GenericResponse,
    IndepMatlInfo,
    MachineState,
    MatlStationInfo,
    Product,
    ProductResponse,
    SlotInfo,
    Temperature,
    ThumbnailResponse,
)
from .tcp import (
    Endstop,
    EndstopStatus,
    FlashForgeTcpClient,
    GCodeController,
    GCodes,
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

# Import TCP classes for low-level access
from .tcp import (
    FlashForgeTcpClient as TcpClient,
)

__version__ = "1.0.0"
__author__ = "FlashForge Python API Contributors"
__email__ = "notghosttypes@gmail.com"
__description__ = "Python library for controlling FlashForge 3D printers"

# Public API - Main classes most users will need
__all__ = [
    # Main client class
    "FlashForgeClient",
    # Data models
    "FFMachineInfo",
    "FFPrinterDetail",
    "FFGcodeFileEntry",
    "FFGcodeToolData",
    "MachineState",
    "Temperature",
    "GenericResponse",
    "DetailResponse",
    "ProductResponse",
    "Product",
    "FilamentArgs",
    # AD5X models
    "SlotInfo",
    "MatlStationInfo",
    "IndepMatlInfo",
    "AD5XMaterialMapping",
    "AD5XLocalJobParams",
    "AD5XSingleColorJobParams",
    "AD5XUploadParams",
    "GCodeListResponse",
    "ThumbnailResponse",
    # Control classes for advanced usage
    "Control",
    "JobControl",
    "Info",
    "Files",
    "TempControl",
    # TCP classes for low-level operations
    "TcpClient",
    "FlashForgeTcpClient",
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
    "GCodes",
    "GCodeController",
    # Discovery classes
    "FlashForgePrinter",
    "FlashForgePrinterDiscovery",
    # Utilities
    "NetworkUtils",
    "FNetCode",
    "Filament",
    "TempWrapper",
    "format_scientific_notation",
    "Endpoints",
    "Commands",
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]

# Convenience imports for common patterns
from .models.machine_info import MachineState as State

# Add version info accessible as flashforge.version
version = __version__
