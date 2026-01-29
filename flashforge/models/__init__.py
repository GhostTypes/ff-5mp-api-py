"""
FlashForge Python API - Models Package
"""

from .machine_info import (
    FFGcodeFileEntry,
    FFGcodeToolData,
    FFMachineInfo,
    FFPrinterDetail,
    IndepMatlInfo,
    MachineState,
    MatlStationInfo,
    SlotInfo,
    Temperature,
)
from .responses import (
    AD5XLocalJobParams,
    AD5XMaterialMapping,
    AD5XSingleColorJobParams,
    AD5XUploadParams,
    DetailResponse,
    FilamentArgs,
    GCodeListResponse,
    GenericResponse,
    Product,
    ProductResponse,
    ThumbnailResponse,
)

__all__ = [
    "FFMachineInfo",
    "FFPrinterDetail",
    "FFGcodeFileEntry",
    "FFGcodeToolData",
    "MachineState",
    "Temperature",
    "SlotInfo",
    "MatlStationInfo",
    "IndepMatlInfo",
    "DetailResponse",
    "FilamentArgs",
    "GenericResponse",
    "Product",
    "ProductResponse",
    "AD5XMaterialMapping",
    "AD5XLocalJobParams",
    "AD5XSingleColorJobParams",
    "AD5XUploadParams",
    "GCodeListResponse",
    "ThumbnailResponse",
]
