"""
Live AD5X Integration Tests

These tests connect to a real FlashForge AD5X printer to verify all AD5X features work correctly.
Tests are skipped if SKIP_LIVE_TESTS=True in printer_config.py.

IMPORTANT:
- Edit tests/printer_config.py with your AD5X printer details before running
- These tests require an actual AD5X printer on your network
- Tests are read-only and will not modify printer state
"""
import pytest
from flashforge import (
    FlashForgeClient,
    AD5XMaterialMapping,
    Filament,
    format_scientific_notation,
    FNetCode
)
from tests.printer_config import get_test_printer_config, skip_if_no_printer


@pytest.mark.asyncio
@skip_if_no_printer("Requires AD5X printer connection")
class TestAD5XLiveConnection:
    """Tests for connecting to AD5X and retrieving details"""

    async def test_connect_and_get_details(self):
        """Test connecting to AD5X and retrieving detailed printer information"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize(), "Failed to initialize client"

            # Verify basic connection
            assert client.printer_name is not None
            assert client.firmware_version is not None
            assert client.mac_address is not None
            assert client.is_ad5x is True, "Printer should be detected as AD5X"

            # Get detailed status
            info = await client.info.get()
            assert info is not None, "Failed to get printer info"

            # Verify AD5X-specific fields
            assert info.is_ad5x is True
            assert info.cooling_fan_left_speed is not None
            assert info.has_matl_station is not None

            # Verify temperature objects exist
            assert info.extruder is not None
            assert info.print_bed is not None
            assert hasattr(info.extruder, 'current')
            assert hasattr(info.extruder, 'set')

    async def test_material_station_info(self):
        """Test retrieving material station information"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            info = await client.info.get()
            assert info is not None

            if info.has_matl_station and info.matl_station_info:
                matl_info = info.matl_station_info

                # Verify material station structure
                assert matl_info.slot_cnt > 0, "Material station should have slots"
                assert 0 <= matl_info.current_slot <= matl_info.slot_cnt
                assert 0 <= matl_info.current_load_slot <= matl_info.slot_cnt
                assert len(matl_info.slot_infos) == matl_info.slot_cnt

                # Verify each slot has valid data
                for slot in matl_info.slot_infos:
                    assert slot.slot_id > 0
                    assert isinstance(slot.has_filament, bool)
                    assert slot.material_name is not None
                    assert slot.material_color is not None
                    # Color should be hex format if not empty
                    if slot.material_color and slot.material_color != '':
                        assert slot.material_color.startswith('#'), f"Color should be hex format: {slot.material_color}"


@pytest.mark.asyncio
@skip_if_no_printer("Requires AD5X printer connection")
class TestAD5XFileOperations:
    """Tests for AD5X file listing and structured data"""

    async def test_get_recent_file_list_structure(self):
        """Test that recent file list returns structured FFGcodeFileEntry objects"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            recent_files = await client.files.get_recent_file_list()
            assert isinstance(recent_files, list), "Should return a list"

            # If there are files, verify structure
            if len(recent_files) > 0:
                entry = recent_files[0]

                # Verify required fields exist
                assert hasattr(entry, 'gcode_file_name')
                assert hasattr(entry, 'printing_time')
                assert entry.gcode_file_name is not None
                assert entry.printing_time >= 0

                # Check AD5X-specific fields if present
                if entry.use_matl_station:
                    assert entry.gcode_tool_cnt is not None
                    assert entry.gcode_tool_cnt > 0

                    if entry.gcode_tool_datas:
                        for tool_data in entry.gcode_tool_datas:
                            assert tool_data.tool_id >= 0
                            assert tool_data.material_name is not None
                            assert tool_data.material_color is not None
                            assert tool_data.filament_weight >= 0

    async def test_get_local_file_list(self):
        """Test retrieving local file list"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            local_files = await client.files.get_local_file_list()
            assert isinstance(local_files, list), "Should return a list"

            # All entries should be strings
            for filename in local_files:
                assert isinstance(filename, str)


@pytest.mark.asyncio
@skip_if_no_printer("Requires AD5X printer connection")
class TestAD5XJobControl:
    """Tests for AD5X job control validation methods"""

    async def test_validate_valid_material_mapping(self):
        """Test that valid material mappings pass validation"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # Create a valid mapping
            valid_mapping = AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FF0000",
                slot_material_color="#FF0000"
            )

            result = client.job_control._validate_material_mappings([valid_mapping])
            assert result is True, "Valid mapping should pass validation"

    async def test_validate_rejects_empty_mappings(self):
        """Test that empty material mappings array is rejected"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            result = client.job_control._validate_material_mappings([])
            assert result is False, "Empty mappings array should fail validation"

    async def test_validate_rejects_too_many_mappings(self):
        """Test that more than 4 mappings are rejected"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            too_many = [
                AD5XMaterialMapping(
                    tool_id=0,
                    slot_id=1,
                    material_name="PLA",
                    tool_material_color="#FF0000",
                    slot_material_color="#FF0000"
                )
                for _ in range(5)
            ]

            result = client.job_control._validate_material_mappings(too_many)
            assert result is False, "More than 4 mappings should fail validation"

    async def test_base64_encoding(self):
        """Test base64 encoding of material mappings"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            mapping = AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

            encoded = client.job_control._encode_material_mappings_to_base64([mapping])

            # Should return a non-empty string
            assert isinstance(encoded, str)
            assert len(encoded) > 0

            # Should be valid base64 (will raise if invalid)
            import base64
            decoded = base64.b64decode(encoded)
            assert len(decoded) > 0

    async def test_ad5x_printer_validation(self):
        """Test that AD5X printer validation works"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # Should pass because we're connected to an AD5X
            result = client.job_control._validate_ad5x_printer()
            assert result is True, "Should validate successfully for AD5X printer"


class TestUtilityClasses:
    """Tests for utility classes (these don't require a live printer)"""

    def test_filament_creation(self):
        """Test Filament class creation"""
        filament = Filament("PLA", 220.0)
        assert filament.name == "PLA"
        assert filament.load_temp == 220.0

    def test_filament_default_temp(self):
        """Test Filament with default temperature"""
        filament = Filament("PLA")
        assert filament.name == "PLA"
        assert filament.load_temp == 220.0

    def test_scientific_notation_small(self):
        """Test scientific notation for small numbers"""
        result = format_scientific_notation(0.0001)
        assert "e" in result.lower()

    def test_scientific_notation_normal(self):
        """Test scientific notation for normal numbers"""
        result = format_scientific_notation(12.34)
        assert "e" not in result.lower()
        assert "12.34" in result

    def test_scientific_notation_large(self):
        """Test scientific notation for large numbers"""
        result = format_scientific_notation(10000)
        assert "e" in result.lower()

    def test_fnet_code_values(self):
        """Test FNetCode enum values"""
        assert FNetCode.OK.value == 0
        assert FNetCode.ERROR.value == 1


@pytest.mark.asyncio
@skip_if_no_printer("Requires AD5X printer connection")
class TestAD5XDetection:
    """Tests for is_ad5x property detection"""

    async def test_is_ad5x_property(self):
        """Test that is_ad5x property is correctly set"""
        config = get_test_printer_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # Should be True for AD5X printer
            assert client.is_ad5x is True, "Client should detect AD5X printer"

            # Info object should also reflect this
            info = await client.info.get()
            assert info is not None
            assert info.is_ad5x is True, "Info object should show is_ad5x=True"
