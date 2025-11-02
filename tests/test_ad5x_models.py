"""
Tests for AD5X Data Models

These tests validate the AD5X-specific data models including:
- AD5XMaterialMapping
- AD5XLocalJobParams
- AD5XSingleColorJobParams
- AD5XUploadParams
- FFGcodeFileEntry
- FFGcodeToolData
- SlotInfo, MatlStationInfo, IndepMatlInfo
"""

import pytest
from pydantic import ValidationError

from flashforge.models.responses import (
    AD5XMaterialMapping,
    AD5XLocalJobParams,
    AD5XSingleColorJobParams,
    AD5XUploadParams,
)
from flashforge.models.machine_info import (
    FFGcodeFileEntry,
    FFGcodeToolData,
    SlotInfo,
    MatlStationInfo,
    IndepMatlInfo,
)


class TestAD5XMaterialMapping:
    """Tests for AD5XMaterialMapping model"""

    def test_create_valid_mapping(self):
        """Test creating a valid material mapping"""
        mapping = AD5XMaterialMapping(
            tool_id=0,
            slot_id=1,
            material_name="PLA",
            tool_material_color="#FFFFFF",
            slot_material_color="#000000"
        )

        assert mapping.tool_id == 0
        assert mapping.slot_id == 1
        assert mapping.material_name == "PLA"
        assert mapping.tool_material_color == "#FFFFFF"
        assert mapping.slot_material_color == "#000000"

    def test_create_all_valid_tool_ids(self):
        """Test creating mappings with all valid toolId values (0-3)"""
        for tool_id in range(4):
            mapping = AD5XMaterialMapping(
                tool_id=tool_id,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
            assert mapping.tool_id == tool_id

    def test_create_all_valid_slot_ids(self):
        """Test creating mappings with all valid slotId values (1-4)"""
        for slot_id in range(1, 5):
            mapping = AD5XMaterialMapping(
                tool_id=0,
                slot_id=slot_id,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
            assert mapping.slot_id == slot_id

    def test_rejects_invalid_tool_id_negative(self):
        """Test Pydantic rejects toolId < 0"""
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=-1,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

    def test_rejects_invalid_tool_id_too_high(self):
        """Test Pydantic rejects toolId > 3"""
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=4,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

    def test_rejects_invalid_slot_id_zero(self):
        """Test Pydantic rejects slotId < 1"""
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=0,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

    def test_rejects_invalid_slot_id_too_high(self):
        """Test Pydantic rejects slotId > 4"""
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=5,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )


class TestAD5XLocalJobParams:
    """Tests for AD5XLocalJobParams model"""

    def test_create_valid_params(self):
        """Test creating valid local job parameters"""
        mapping = AD5XMaterialMapping(
            tool_id=0,
            slot_id=1,
            material_name="PLA",
            tool_material_color="#FFFFFF",
            slot_material_color="#000000"
        )

        params = AD5XLocalJobParams(
            file_name="test.gcode",
            leveling_before_print=True,
            material_mappings=[mapping]
        )

        assert params.file_name == "test.gcode"
        assert params.leveling_before_print is True
        assert len(params.material_mappings) == 1

    def test_create_with_multiple_mappings(self):
        """Test creating params with multiple material mappings"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=i,
                slot_id=i + 1,
                material_name=f"Material{i}",
                tool_material_color="#FF0000",
                slot_material_color="#00FF00"
            )
            for i in range(3)
        ]

        params = AD5XLocalJobParams(
            file_name="multi.gcode",
            leveling_before_print=False,
            material_mappings=mappings
        )

        assert len(params.material_mappings) == 3


class TestAD5XSingleColorJobParams:
    """Tests for AD5XSingleColorJobParams model"""

    def test_create_valid_params(self):
        """Test creating valid single-color job parameters"""
        params = AD5XSingleColorJobParams(
            file_name="single_color.gcode",
            leveling_before_print=True
        )

        assert params.file_name == "single_color.gcode"
        assert params.leveling_before_print is True

    def test_create_without_leveling(self):
        """Test creating params without bed leveling"""
        params = AD5XSingleColorJobParams(
            file_name="test.gcode",
            leveling_before_print=False
        )

        assert params.leveling_before_print is False


class TestAD5XUploadParams:
    """Tests for AD5XUploadParams model"""

    def test_create_valid_upload_params(self):
        """Test creating valid upload parameters"""
        mapping = AD5XMaterialMapping(
            tool_id=0,
            slot_id=1,
            material_name="PLA",
            tool_material_color="#FFFFFF",
            slot_material_color="#000000"
        )

        params = AD5XUploadParams(
            file_path="/path/to/file.gcode",
            start_print=True,
            leveling_before_print=True,
            flow_calibration=False,
            first_layer_inspection=True,
            time_lapse_video=False,
            material_mappings=[mapping]
        )

        assert params.file_path == "/path/to/file.gcode"
        assert params.start_print is True
        assert params.leveling_before_print is True
        assert params.flow_calibration is False
        assert params.first_layer_inspection is True
        assert params.time_lapse_video is False
        assert len(params.material_mappings) == 1

    def test_create_with_all_options_enabled(self):
        """Test creating params with all boolean options enabled"""
        mapping = AD5XMaterialMapping(
            tool_id=0,
            slot_id=1,
            material_name="PLA",
            tool_material_color="#FFFFFF",
            slot_material_color="#000000"
        )

        params = AD5XUploadParams(
            file_path="/test.gcode",
            start_print=True,
            leveling_before_print=True,
            flow_calibration=True,
            first_layer_inspection=True,
            time_lapse_video=True,
            material_mappings=[mapping]
        )

        assert all([
            params.start_print,
            params.leveling_before_print,
            params.flow_calibration,
            params.first_layer_inspection,
            params.time_lapse_video
        ])


class TestFFGcodeFileEntry:
    """Tests for FFGcodeFileEntry model"""

    def test_create_basic_entry(self):
        """Test creating basic file entry (older printer format)"""
        entry = FFGcodeFileEntry(
            gcode_file_name="test.gcode",
            printing_time=3600
        )

        assert entry.gcode_file_name == "test.gcode"
        assert entry.printing_time == 3600
        assert entry.gcode_tool_cnt is None
        assert entry.use_matl_station is None

    def test_create_ad5x_entry_with_materials(self):
        """Test creating AD5X file entry with material info"""
        tool_data = FFGcodeToolData(
            filament_weight=50.5,
            material_color="#FF0000",
            material_name="PLA",
            slot_id=1,
            tool_id=0
        )

        entry = FFGcodeFileEntry(
            gcode_file_name="multi_color.3mf",
            printing_time=7200,
            gcode_tool_cnt=2,
            gcode_tool_datas=[tool_data],
            total_filament_weight=100.5,
            use_matl_station=True
        )

        assert entry.gcode_file_name == "multi_color.3mf"
        assert entry.printing_time == 7200
        assert entry.gcode_tool_cnt == 2
        assert len(entry.gcode_tool_datas) == 1
        assert entry.total_filament_weight == 100.5
        assert entry.use_matl_station is True

    def test_parse_from_dict_with_aliases(self):
        """Test parsing from dict using camelCase aliases"""
        data = {
            "gcodeFileName": "test.gcode",
            "printingTime": 1800,
            "gcodeToolCnt": 1,
            "totalFilamentWeight": 25.0,
            "useMatlStation": False
        }

        entry = FFGcodeFileEntry(**data)

        assert entry.gcode_file_name == "test.gcode"
        assert entry.printing_time == 1800
        assert entry.gcode_tool_cnt == 1
        assert entry.total_filament_weight == 25.0
        assert entry.use_matl_station is False


class TestFFGcodeToolData:
    """Tests for FFGcodeToolData model"""

    def test_create_tool_data(self):
        """Test creating tool/material data"""
        tool_data = FFGcodeToolData(
            filament_weight=25.5,
            material_color="#FF0000",
            material_name="PLA",
            slot_id=2,
            tool_id=1
        )

        assert tool_data.filament_weight == 25.5
        assert tool_data.material_color == "#FF0000"
        assert tool_data.material_name == "PLA"
        assert tool_data.slot_id == 2
        assert tool_data.tool_id == 1

    def test_parse_from_dict_with_aliases(self):
        """Test parsing from dict using camelCase aliases"""
        data = {
            "filamentWeight": 30.0,
            "materialColor": "#00FF00",
            "materialName": "PETG",
            "slotId": 3,
            "toolId": 2
        }

        tool_data = FFGcodeToolData(**data)

        assert tool_data.filament_weight == 30.0
        assert tool_data.material_color == "#00FF00"
        assert tool_data.material_name == "PETG"
        assert tool_data.slot_id == 3
        assert tool_data.tool_id == 2


class TestSlotInfo:
    """Tests for SlotInfo model"""

    def test_create_slot_info(self):
        """Test creating slot info"""
        slot = SlotInfo(
            has_filament=True,
            material_color="#FF0000",
            material_name="PLA",
            slot_id=1
        )

        assert slot.has_filament is True
        assert slot.material_color == "#FF0000"
        assert slot.material_name == "PLA"
        assert slot.slot_id == 1

    def test_create_empty_slot(self):
        """Test creating empty slot info"""
        slot = SlotInfo(
            has_filament=False,
            material_color="",
            material_name="",
            slot_id=2
        )

        assert slot.has_filament is False
        assert slot.material_color == ""
        assert slot.material_name == ""


class TestMatlStationInfo:
    """Tests for MatlStationInfo model"""

    def test_create_station_info(self):
        """Test creating material station info"""
        slots = [
            SlotInfo(
                has_filament=True,
                material_color="#FF0000",
                material_name="PLA",
                slot_id=i + 1
            )
            for i in range(4)
        ]

        station = MatlStationInfo(
            current_load_slot=0,
            current_slot=1,
            slot_cnt=4,
            slot_infos=slots,
            state_action=0,
            state_step=0
        )

        assert station.current_load_slot == 0
        assert station.current_slot == 1
        assert station.slot_cnt == 4
        assert len(station.slot_infos) == 4
        assert station.state_action == 0
        assert station.state_step == 0


class TestIndepMatlInfo:
    """Tests for IndepMatlInfo model"""

    def test_create_indep_matl_info(self):
        """Test creating independent material info"""
        info = IndepMatlInfo(
            material_color="#00FF00",
            material_name="PETG",
            state_action=1,
            state_step=2
        )

        assert info.material_color == "#00FF00"
        assert info.material_name == "PETG"
        assert info.state_action == 1
        assert info.state_step == 2

    def test_create_with_unknown_material(self):
        """Test creating info with unknown material"""
        info = IndepMatlInfo(
            material_color="",
            material_name="?",
            state_action=0,
            state_step=0
        )

        assert info.material_name == "?"
