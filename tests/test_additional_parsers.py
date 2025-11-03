"""
Additional parser unit tests.
"""
import pytest

from flashforge.tcp.parsers.location_info import LocationInfo
from flashforge.tcp.parsers.printer_info import PrinterInfo
from flashforge.tcp.parsers.temp_info import TempInfo


def test_parse_valid_location_response():
    """LocationInfo parses coordinates correctly."""
    replay = "ok M114\nX:100.00 Y:150.00 Z:10.50\nok\n"
    info = LocationInfo().from_replay(replay)
    assert info is not None
    assert info.x == "100.00"
    assert info.y == "150.00"
    assert info.z == "10.50"


def test_parse_invalid_location_response():
    """Invalid responses return None."""
    replay = "bad data"
    info = LocationInfo().from_replay(replay)
    assert info is None


def test_parse_valid_temp_response():
    """TempInfo parses extruder and bed temperatures."""
    replay = "ok M105\nT0:220/220 B:60/60 @:0 B@:0\nok\n"
    info = TempInfo().from_replay(replay)
    assert info is not None
    extruder = info.get_extruder_temp()
    bed = info.get_bed_temp()
    assert extruder.get_current() == 220
    assert extruder.get_set() == 220
    assert bed.get_current() == 60


def test_parse_temp_response_cooling():
    """Cooling temps with zero targets parsed correctly."""
    replay = "ok M105\nT0:50/0 B:30/0 @:0 B@:0\nok\n"
    info = TempInfo().from_replay(replay)
    assert info is not None
    extruder = info.get_extruder_temp()
    bed = info.get_bed_temp()
    assert extruder.get_current() == 50
    assert bed.get_current() == 30
    assert bed.get_set() == 0


def test_parse_printer_info_complete():
    """PrinterInfo parses complete responses."""
    replay = (
        "ok M115\n"
        "Machine Type: Adventurer 5M Pro\n"
        "Machine Name: Shop Printer\n"
        "Firmware: V3.2.0\n"
        "SN: SNMOMC9900728\n"
        "X:220 Y:220 Z:220\n"
        "Tool count: 1\n"
        "Mac Address:11:22:33:44:55:66\n"
    )
    info = PrinterInfo().from_replay(replay)
    assert info is not None
    assert info.type_name == "Adventurer 5M Pro"
    assert info.name == "Shop Printer"
    assert info.firmware_version == "V3.2.0"
    assert info.serial_number == "SNMOMC9900728"
    assert info.tool_count == "1"


def test_parse_printer_info_minimal():
    """Minimal responses still parse required fields."""
    replay = (
        "ok M115\n"
        "Machine Type: Adventurer\n"
        "Machine Name: Bench\n"
        "Firmware: V1.0.0\n"
        "SN: SN123\n"
    )
    info = PrinterInfo().from_replay(replay)
    assert info is not None
    assert info.type_name == "Adventurer"
    assert info.name == "Bench"
    assert info.firmware_version == "V1.0.0"
    assert info.serial_number == "SN123"
