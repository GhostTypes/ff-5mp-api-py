"""
Tests for Utility Classes

These tests validate the utility classes added for TypeScript parity:
- Filament class
- Temperature wrapper class
- format_scientific_notation() function
- FNetCode enum
"""

import pytest
from flashforge.api.filament import Filament
from flashforge.api.misc import Temperature, format_scientific_notation
from flashforge.api.network.fnet_code import FNetCode


class TestFilament:
    """Tests for the Filament class"""

    def test_create_with_defaults(self):
        """Test creating Filament with default temperature"""
        filament = Filament("PLA")

        assert filament.name == "PLA"
        assert filament.load_temp == 220.0

    def test_create_with_custom_temp(self):
        """Test creating Filament with custom temperature"""
        filament = Filament("ABS", 240.0)

        assert filament.name == "ABS"
        assert filament.load_temp == 240.0

    def test_create_with_various_materials(self):
        """Test creating Filament with various material types"""
        materials = [
            ("PLA", 200.0),
            ("ABS", 240.0),
            ("PETG", 230.0),
            ("TPU", 210.0),
            ("Nylon", 250.0),
        ]

        for name, temp in materials:
            filament = Filament(name, temp)
            assert filament.name == name
            assert filament.load_temp == temp

    def test_properties_are_readonly(self):
        """Test that Filament properties cannot be modified after creation"""
        filament = Filament("PLA", 220.0)

        # Properties should be read-only
        with pytest.raises(AttributeError):
            filament.name = "ABS"

        with pytest.raises(AttributeError):
            filament.load_temp = 240.0

    def test_repr(self):
        """Test __repr__ method"""
        filament = Filament("PLA", 220.0)
        repr_str = repr(filament)

        assert "Filament" in repr_str
        assert "PLA" in repr_str
        assert "220" in repr_str

    def test_str(self):
        """Test __str__ method"""
        filament = Filament("PLA", 220.0)
        str_repr = str(filament)

        assert "PLA" in str_repr
        assert "220" in str_repr
        assert "°C" in str_repr


class TestTemperatureWrapper:
    """Tests for the Temperature wrapper class"""

    def test_create_with_value(self):
        """Test creating Temperature with a value"""
        temp = Temperature(25.5)
        assert temp.get_value() == 25.5

    def test_create_with_zero(self):
        """Test creating Temperature with zero"""
        temp = Temperature(0)
        assert temp.get_value() == 0

    def test_create_with_negative(self):
        """Test creating Temperature with negative value"""
        temp = Temperature(-10.5)
        assert temp.get_value() == -10.5

    def test_create_with_high_temp(self):
        """Test creating Temperature with high value"""
        temp = Temperature(300.0)
        assert temp.get_value() == 300.0

    def test_str_conversion(self):
        """Test __str__ method"""
        temp = Temperature(25.5)
        assert str(temp) == "25.5"

    def test_str_conversion_integer(self):
        """Test __str__ with integer value"""
        temp = Temperature(25)
        assert str(temp) == "25"

    def test_repr(self):
        """Test __repr__ method"""
        temp = Temperature(25.5)
        repr_str = repr(temp)

        assert "Temperature" in repr_str
        assert "25.5" in repr_str


class TestFormatScientificNotation:
    """Tests for the format_scientific_notation() function"""

    def test_very_small_number_uses_scientific(self):
        """Test that very small numbers use scientific notation"""
        result = format_scientific_notation(0.0001)
        assert "e" in result.lower()

    def test_very_large_number_uses_scientific(self):
        """Test that very large numbers use scientific notation"""
        result = format_scientific_notation(10000)
        assert "e" in result.lower()

    def test_normal_number_uses_standard(self):
        """Test that normal numbers use standard notation"""
        result = format_scientific_notation(12.34)
        assert "e" not in result.lower()
        assert "12.34" in result

    def test_boundary_small_uses_scientific(self):
        """Test boundary case: 0.001 should NOT use scientific"""
        result = format_scientific_notation(0.001)
        # At exactly 0.001, should be standard format
        assert "e" not in result.lower()

    def test_just_below_boundary_small_uses_scientific(self):
        """Test just below small boundary uses scientific"""
        result = format_scientific_notation(0.0009)
        assert "e" in result.lower()

    def test_boundary_large_uses_scientific(self):
        """Test boundary case: 10000 uses scientific"""
        result = format_scientific_notation(10000)
        assert "e" in result.lower()

    def test_just_below_boundary_large_uses_standard(self):
        """Test just below large boundary uses standard"""
        result = format_scientific_notation(9999.99)
        assert "e" not in result.lower()

    def test_zero(self):
        """Test zero value - Python's :e format uses scientific for 0"""
        result = format_scientific_notation(0)
        # Python formats 0 as 0.000000e+00 with :e format
        assert "e" in result.lower() or result == "0"

    def test_negative_small_number(self):
        """Test negative very small number"""
        result = format_scientific_notation(-0.0001)
        assert "e" in result.lower()

    def test_negative_large_number(self):
        """Test negative very large number"""
        result = format_scientific_notation(-10000)
        assert "e" in result.lower()

    def test_negative_normal_number(self):
        """Test negative normal number"""
        result = format_scientific_notation(-12.34)
        assert "e" not in result.lower()

    def test_various_normal_numbers(self):
        """Test various numbers in the normal range"""
        normal_numbers = [0.001, 0.5, 1.0, 10.0, 100.0, 1000.0, 9999.0]

        for num in normal_numbers:
            result = format_scientific_notation(num)
            assert "e" not in result.lower(), \
                f"Number {num} should use standard format, got: {result}"

    def test_various_scientific_numbers(self):
        """Test various numbers that should use scientific notation"""
        scientific_numbers = [0.0000001, 0.0005, 10001, 1000000, 1e10]

        for num in scientific_numbers:
            result = format_scientific_notation(num)
            assert "e" in result.lower(), \
                f"Number {num} should use scientific format, got: {result}"


class TestFNetCode:
    """Tests for the FNetCode enum"""

    def test_ok_value(self):
        """Test FNetCode.OK has value 0"""
        assert FNetCode.OK.value == 0

    def test_error_value(self):
        """Test FNetCode.ERROR has value 1"""
        assert FNetCode.ERROR.value == 1

    def test_enum_members(self):
        """Test enum has exactly 2 members"""
        assert len(FNetCode) == 2

    def test_enum_comparison(self):
        """Test enum members can be compared"""
        assert FNetCode.OK == FNetCode.OK
        assert FNetCode.ERROR == FNetCode.ERROR
        assert FNetCode.OK != FNetCode.ERROR

    def test_enum_access_by_value(self):
        """Test accessing enum by value"""
        assert FNetCode(0) == FNetCode.OK
        assert FNetCode(1) == FNetCode.ERROR

    def test_enum_access_by_name(self):
        """Test accessing enum by name"""
        assert FNetCode["OK"] == FNetCode.OK
        assert FNetCode["ERROR"] == FNetCode.ERROR
