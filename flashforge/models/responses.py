"""
FlashForge Python API - Response Models
"""

from typing import Optional, Union
from pydantic import BaseModel, Field

from .machine_info import FFPrinterDetail, FFGcodeFileEntry


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


class AD5XMaterialMapping(BaseModel):
    """Represents a material mapping for AD5X multi-color printing. Maps a tool (extruder) to a specific material station slot."""
    tool_id: int = Field(ge=0, le=3, description="Tool ID (0-based: 0, 1, 2, 3)")
    slot_id: int = Field(ge=1, le=4, description="Slot ID (1-based: 1, 2, 3, 4)")
    material_name: str = Field(description="Name of the material (e.g., 'PLA', 'SILK')")
    tool_material_color: str = Field(description="Hex color code for the tool material (e.g., '#FFFFFF')")
    slot_material_color: str = Field(description="Hex color code for the slot material (e.g., '#46328E')")

    class Config:
        populate_by_name = True


class AD5XLocalJobParams(BaseModel):
    """Parameters for starting an AD5X local job with material mappings. Used for multi-color prints that utilize the material station."""
    file_name: str = Field(description="Name of the file on the printer to start")
    leveling_before_print: bool = Field(description="Whether to perform bed leveling before printing")
    material_mappings: list[AD5XMaterialMapping] = Field(description="Array of material mappings (1-4 items)")

    class Config:
        populate_by_name = True


class AD5XSingleColorJobParams(BaseModel):
    """Parameters for starting an AD5X single-color local job. Used for single-color prints that do not require the material station."""
    file_name: str = Field(description="Name of the file on the printer to start")
    leveling_before_print: bool = Field(description="Whether to perform bed leveling before printing")

    class Config:
        populate_by_name = True


class AD5XUploadParams(BaseModel):
    """Parameters for uploading a file to AD5X printer with material station support. Extends basic upload functionality with AD5X-specific features."""
    file_path: str = Field(description="Local file path to upload")
    start_print: bool = Field(description="Whether to start printing immediately after upload")
    leveling_before_print: bool = Field(description="Whether to perform bed leveling before printing")
    flow_calibration: bool = Field(description="Whether to enable flow calibration")
    first_layer_inspection: bool = Field(description="Whether to enable first layer inspection")
    time_lapse_video: bool = Field(description="Whether to enable time lapse video recording")
    material_mappings: list[AD5XMaterialMapping] = Field(description="Array of material mappings for the material station (1-4 items)")

    class Config:
        populate_by_name = True


class GCodeListResponse(GenericResponse):
    """Represents the response structure for a G-code file list request."""
    gcode_list: Optional[Union[list[str], list[FFGcodeFileEntry]]] = Field(default=None, alias="gcodeList")
    gcode_list_detail: Optional[list[FFGcodeFileEntry]] = Field(default=None, alias="gcodeListDetail")

    class Config:
        populate_by_name = True


class ThumbnailResponse(GenericResponse):
    """Represents the response structure for a G-code thumbnail request."""
    image_data: str = Field(alias="imageData", description="The thumbnail image data encoded as a base64 string")

    class Config:
        populate_by_name = True
