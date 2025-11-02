"""
FlashForge Python API - Models Package
"""
from .machine_info import (
    FFMachineInfo,
    FFPrinterDetail,
    FFGcodeFileEntry,
    FFGcodeToolData,
    MachineState,
    Temperature,
    SlotInfo,
    MatlStationInfo,
    IndepMatlInfo,
)
from .responses import (
    DetailResponse,
    FilamentArgs,
    GenericResponse,
    Product,
    ProductResponse,
    AD5XMaterialMapping,
    AD5XLocalJobParams,
    AD5XSingleColorJobParams,
    AD5XUploadParams,
    GCodeListResponse,
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
