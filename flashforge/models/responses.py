"""
FlashForge Python API - Response Models
"""

from pydantic import BaseModel

from .machine_info import FFPrinterDetail


class GenericResponse(BaseModel):
    """Represents a generic response from the printer's API."""
    code: int
    message: str = ""


class DetailResponse(GenericResponse):
    """Represents the structure of the response from the printer's detail endpoint."""
    detail: FFPrinterDetail


class Product(BaseModel):
    """
    Defines the structure of the `product` object nested within a `ProductResponse`.
    
    This contains various control state flags reported by the printer,
    indicating the status or availability of certain features like temperature controls,
    fan controls, and light controls. A state of 0 often means off/unavailable,
    while other numbers (typically 1) mean on/available or a specific mode.
    
    Field names match the actual camelCase format returned by the printer.
    """
    chamberTempCtrlState: int
    externalFanCtrlState: int
    internalFanCtrlState: int
    lightCtrlState: int
    nozzleTempCtrlState: int
    platformTempCtrlState: int


class ProductResponse(GenericResponse):
    """
    Represents the expected structure of the response from the "product command"
    sent to the printer (typically to the `/product` endpoint).
    
    This response includes general status information (via `GenericResponse`)
    and a nested `product` object containing specific control states.
    """
    product: Product


class FilamentArgs(BaseModel):
    """Represents the arguments for controlling the printer's filtration system."""
    internal: str
    external: str

    def __init__(self, internal_on: bool, external_on: bool):
        super().__init__(
            internal="open" if internal_on else "close",
            external="open" if external_on else "close"
        )
