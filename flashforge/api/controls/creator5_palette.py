"""
FlashForge Python API - Creator 5 / Creator 5 Pro material-station slot color
palette and perceptual nearest-color snapping.

The Creator 5 ``msConfig_cmd`` only renders a color icon when the ``rgb`` field is
an EXACT, case-sensitive, byte-for-byte match against one of the firmware's 24
built-in palette strings (compared via ``std::operator==`` in ``firmwareExe``
1.9.2). A non-match leaves the slot's color index at 0 (White). These values
DIFFER from the AD5X palette (e.g. Blue is ``#4CAAF8`` here vs ``#45A8F9`` on the
AD5X), so callers must snap against THIS list specifically.

By contrast the AD5X accepts freeform hex (with the ``#`` stripped), so the two
wire formats are mutually exclusive — see :func:`flashforge.api.controls.control.Control.configure_slot`
for the model-gating that splits them.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

# The color-space math in this module mirrors the published CIEDE2000 / CIE L*a*b*
# notation (L, a, b, C', h', etc.) verbatim so it can be checked against the
# reference. PEP 8 lowercase locals are therefore relaxed here on purpose.
# ruff: noqa: N806


@dataclass(frozen=True)
class Creator5PaletteColor:
    """A single entry in the Creator 5 firmware color palette."""

    index: int
    """Firmware palette index (0 = White = the no-match fallback)."""

    name: str
    """Color name as shown on the printer UI."""

    hex: str  # noqa: N815 - field mirrors the TS `hex` property name
    """Wire value sent to the printer, always uppercase ``#RRGGBB``."""


#: The firmware's 24-entry UI palette (firmwareExe 1.9.2, Ghidra-confirmed).
#: Index 0 (White) is also what the firmware falls back to on a no-match.
CREATOR5_PALETTE: tuple[Creator5PaletteColor, ...] = (
    Creator5PaletteColor(0, "White", "#FFFFFF"),
    Creator5PaletteColor(1, "Yellow", "#FFF245"),
    Creator5PaletteColor(2, "Light Green", "#DEF578"),
    Creator5PaletteColor(3, "Green", "#21CC3D"),
    Creator5PaletteColor(4, "Dark Green", "#167A4B"),
    Creator5PaletteColor(5, "Teal", "#156682"),
    Creator5PaletteColor(6, "Cyan", "#24E4A0"),
    Creator5PaletteColor(7, "Light Blue", "#7BD9F0"),
    Creator5PaletteColor(8, "Blue", "#4CAAF8"),
    Creator5PaletteColor(9, "Dark Blue", "#2E54DD"),
    Creator5PaletteColor(10, "Purple", "#48358C"),
    Creator5PaletteColor(11, "Violet", "#A341F7"),
    Creator5PaletteColor(12, "Magenta", "#F435F6"),
    Creator5PaletteColor(13, "Pink", "#D5B4DE"),
    Creator5PaletteColor(14, "Coral", "#FA6173"),
    Creator5PaletteColor(15, "Red", "#F82D29"),
    Creator5PaletteColor(16, "Brown", "#805003"),
    Creator5PaletteColor(17, "Orange", "#F9903B"),
    Creator5PaletteColor(18, "Cream", "#FCEBD7"),
    Creator5PaletteColor(19, "Tan", "#D5C5A1"),
    Creator5PaletteColor(20, "Dark Brown", "#B17C38"),
    Creator5PaletteColor(21, "Gray", "#8C8C89"),
    Creator5PaletteColor(22, "Light Gray", "#BEBEBE"),
    Creator5PaletteColor(23, "Black", "#1B1B1B"),
)

# 25^7, the CIEDE2000 chroma weighting constant.
_25_POW_7 = 25.0 ** 7

# D65 reference white point used by the sRGB -> XYZ transform.
_D65_XN = 0.95047
_D65_YN = 1.0
_D65_ZN = 1.08883


def _srgb_to_linear(channel: float) -> float:
    """sRGB component (0-255) channel transfer function -> linear value (0-1)."""
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb_to_lab(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    Converts an sRGB color (0-255 channels) to CIE L*a*b* under a D65 illuminant.
    Used as the perceptual basis for the CIEDE2000 nearest-color match.
    """
    R = _srgb_to_linear(r)
    G = _srgb_to_linear(g)
    B = _srgb_to_linear(b)

    x = R * 0.4124564 + G * 0.3575761 + B * 0.1804375
    y = R * 0.2126729 + G * 0.7151522 + B * 0.072175
    z = R * 0.0193339 + G * 0.119192 + B * 0.9503041

    x /= _D65_XN
    y /= _D65_YN
    z /= _D65_ZN

    def f(t: float) -> float:
        return math.cbrt(t) if t > 0.008856 else 7.787 * t + 16.0 / 116.0

    fx = f(x)
    fy = f(y)
    fz = f(z)

    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def _atan2_deg(ordinate: float, abscissa: float) -> float:
    """atan2 -> hue in degrees, normalized to [0, 360)."""
    h = math.degrees(math.atan2(ordinate, abscissa))
    if h < 0:
        h += 360.0
    return h


def _delta_e_2000(c1: tuple[float, float, float], c2: tuple[float, float, float]) -> float:
    """
    CIEDE2000 color difference between two L*a*b* colors (kL=kC=kH=1). This is the
    most accurate standard delta-E metric and is preferred here because the
    firmware renders only an exact palette match — snapping to the wrong
    perceptual neighbor would display the wrong color on the printer.
    """
    L1, a1, b1 = c1
    L2, a2, b2 = c2

    C1 = math.sqrt(a1 * a1 + b1 * b1)
    C2 = math.sqrt(a2 * a2 + b2 * b2)
    Cbar = (C1 + C2) / 2.0
    Cbar7 = Cbar ** 7
    G = 0.5 * (1 - math.sqrt(Cbar7 / (Cbar7 + _25_POW_7)))

    a1p = (1 + G) * a1
    a2p = (1 + G) * a2
    C1p = math.sqrt(a1p * a1p + b1 * b1)
    C2p = math.sqrt(a2p * a2p + b2 * b2)
    h1p = _atan2_deg(b1, a1p)
    h2p = _atan2_deg(b2, a2p)

    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        diff = h2p - h1p
        if abs(diff) <= 180:
            dhp = diff
        elif diff > 180:
            dhp = diff - 360
        else:
            dhp = diff + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2.0)

    Lbarp = (L1 + L2) / 2.0
    Cbarp = (C1p + C2p) / 2.0
    if C1p * C2p == 0:
        hbarp = h1p + h2p
    else:
        diff = abs(h1p - h2p)
        if diff <= 180:
            hbarp = (h1p + h2p) / 2.0
        elif h1p + h2p < 360:
            hbarp = (h1p + h2p + 360) / 2.0
        else:
            hbarp = (h1p + h2p - 360) / 2.0

    T = (
        1
        - 0.17 * math.cos(math.radians(hbarp - 30))
        + 0.24 * math.cos(math.radians(2 * hbarp))
        + 0.32 * math.cos(math.radians(3 * hbarp + 6))
        - 0.20 * math.cos(math.radians(4 * hbarp - 63))
    )

    dTheta = 30 * math.exp(-(((hbarp - 275) / 25.0) ** 2))
    Cbarp7 = Cbarp ** 7
    RC = 2 * math.sqrt(Cbarp7 / (Cbarp7 + _25_POW_7))
    SL = 1 + (0.015 * (Lbarp - 50) ** 2) / math.sqrt(20 + (Lbarp - 50) ** 2)
    SC = 1 + 0.045 * Cbarp
    SH = 1 + 0.015 * Cbarp * T
    RT = -math.sin(math.radians(2 * dTheta)) * RC

    termL = dLp / SL
    termC = dCp / SC
    termH = dHp / SH

    return math.sqrt(termL * termL + termC * termC + termH * termH + RT * termC * termH)


_HEX_RE = re.compile(r"^[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int] | None:
    """
    Parses a hex color string (``#RRGGBB``, ``RRGGBB``, 3-digit shorthand, any
    case) into its RGB channels. Returns None for unparseable input.
    """
    clean = hex_str.strip()
    # Remove a single leading "#" (matches the TS replace(/^#/, '')).
    if clean.startswith("#"):
        clean = clean[1:]
    if not _HEX_RE.match(clean):
        return None
    if len(clean) == 3:
        clean = "".join(ch + ch for ch in clean)
    return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


# Palette entries with their L*a*b* values precomputed once at module load.
_PALETTE_LAB: list[tuple[Creator5PaletteColor, tuple[float, float, float]]] = []
for _color in CREATOR5_PALETTE:
    _rgb = _hex_to_rgb(_color.hex)
    if _rgb is None:
        _rgb = (0, 0, 0)
    _PALETTE_LAB.append((_color, _rgb_to_lab(_rgb[0], _rgb[1], _rgb[2])))


def snap_to_creator5_palette(hex_str: str) -> Creator5PaletteColor:
    """
    Snaps an arbitrary hex color to the nearest entry in the Creator 5 firmware
    palette using the CIEDE2000 perceptual distance in CIE L*a*b* space.

    The returned :attr:`Creator5PaletteColor.hex` is always uppercase ``#RRGGBB``
    and is guaranteed to be a byte-for-byte firmware match. Unparseable input
    falls back to White (index 0, the firmware's own no-match fallback) with a
    warning.

    Args:
        hex_str: The caller's color as a hex string (leading ``#`` optional, any case).

    Returns:
        The nearest Creator 5 palette entry.
    """
    rgb = _hex_to_rgb(hex_str)
    if rgb is None:
        print(
            f'snap_to_creator5_palette: could not parse "{hex_str}" as hex; '
            "falling back to White."
        )
        return CREATOR5_PALETTE[0]

    target = _rgb_to_lab(rgb[0], rgb[1], rgb[2])
    best = _PALETTE_LAB[0]
    best_delta = float("inf")
    for entry in _PALETTE_LAB:
        delta = _delta_e_2000(target, entry[1])
        if delta < best_delta:
            best_delta = delta
            best = entry
    return best[0]
