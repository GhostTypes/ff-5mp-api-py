"""
FlashForge Python API - 3MF support

Parse a sliced ``.3mf`` before upload to learn which tools and materials the
print uses. See :func:`parse_3mf`.
"""

from .parser import (
    MAX_GCODE_HEADER_BYTES,
    MAX_SLICE_INFO_BYTES,
    MAX_THUMBNAIL_BYTES,
    PrinterFamily,
    ThreeMFError,
    ThreeMFFilament,
    ThreeMFFile,
    ThreeMFFormatError,
    ThreeMFMultiplePlatesError,
    ThreeMFNotSlicedError,
    ThreeMFWarning,
    parse_3mf,
    printer_family_from_model_id,
)
from .warnings import translate_warning

__all__ = [
    "MAX_GCODE_HEADER_BYTES",
    "MAX_SLICE_INFO_BYTES",
    "MAX_THUMBNAIL_BYTES",
    "PrinterFamily",
    "ThreeMFError",
    "ThreeMFFilament",
    "ThreeMFFile",
    "ThreeMFFormatError",
    "ThreeMFMultiplePlatesError",
    "ThreeMFNotSlicedError",
    "ThreeMFWarning",
    "parse_3mf",
    "printer_family_from_model_id",
    "translate_warning",
]
