"""
Unit tests for the Creator 5 palette + nearest-color snapping.

Verifies the CIEDE2000 perceptual snap produces byte-for-byte firmware palette
matches (exact, case-sensitive "#RRGGBB") for the msConfig_cmd wire format.
Mirrors src/api/controls/creator5Palette.test.ts.
"""

import re

import pytest

from flashforge.api.controls.creator5_palette import (
    CREATOR5_PALETTE,
    Creator5PaletteColor,
    snap_to_creator5_palette,
)

_HEX_RE = re.compile(r"^#[0-9A-F]{6}$")


def test_palette_has_24_entries_all_uppercase_index_zero_white():
    """The palette has exactly 24 entries, all uppercase "#RRGGBB", index 0 = White."""
    assert len(CREATOR5_PALETTE) == 24
    for color in CREATOR5_PALETTE:
        assert _HEX_RE.match(color.hex)
        assert color.hex == color.hex.upper()
    assert CREATOR5_PALETTE[0] == Creator5PaletteColor(0, "White", "#FFFFFF")


def test_every_palette_entry_snaps_to_itself():
    """Every palette entry snaps to itself."""
    for color in CREATOR5_PALETTE:
        assert snap_to_creator5_palette(color.hex).hex == color.hex


@pytest.mark.parametrize(
    "hex_input",
    ["#FF0000", "#123456", "#00FF00", "#ABCDEF", "#112233", "#FEDCBA", "#8080FF"],
)
def test_never_returns_off_palette_value(hex_input):
    """snap never returns an off-palette value."""
    palette_hexes = [c.hex for c in CREATOR5_PALETTE]
    snapped = snap_to_creator5_palette(hex_input).hex
    assert snapped in palette_hexes


@pytest.mark.parametrize("hex_input", ["#ff0000", "ff0000", "#4caaf8", "4CAAf8", "#abc"])
def test_always_returns_uppercase_with_leading_hash(hex_input):
    """snap always returns uppercase "#RRGGBB" with the leading "#"."""
    snapped = snap_to_creator5_palette(hex_input).hex
    assert _HEX_RE.match(snapped)


def test_snaps_pure_red_to_palette_red():
    """Pure red #FF0000 snaps to palette Red #F82D29."""
    assert snap_to_creator5_palette("#FF0000").hex == "#F82D29"


@pytest.mark.parametrize("hex_input", ["#4CAAF8", "#4caaf8", "4caaF8"])
def test_exact_palette_entry_snaps_to_itself_regardless_of_case(hex_input):
    """An exact palette entry snaps to itself regardless of input case/shape."""
    assert snap_to_creator5_palette(hex_input).hex == "#4CAAF8"


def test_snaps_white_to_ffffff():
    """White snaps to #FFFFFF (3-digit shorthand too)."""
    assert snap_to_creator5_palette("#FFFFFF").hex == "#FFFFFF"
    assert snap_to_creator5_palette("#FFF").hex == "#FFFFFF"


@pytest.mark.parametrize("hex_input", ["not-a-color", ""])
def test_falls_back_to_white_on_unparseable_input(hex_input):
    """Unparseable input falls back to White (index 0)."""
    assert snap_to_creator5_palette(hex_input) == CREATOR5_PALETTE[0]
