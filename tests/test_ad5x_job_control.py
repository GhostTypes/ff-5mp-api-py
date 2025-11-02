"""
Tests for AD5X Job Control functionality

These tests validate the AD5X-specific job control methods including
material mapping validation, base64 encoding, and printer validation.
"""

import base64
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch

from flashforge.api.controls.job_control import JobControl
from flashforge.models.responses import AD5XMaterialMapping


class TestMaterialMappingValidation:
    """Tests for _validate_material_mappings() method"""

    def setup_method(self):
        """Create a JobControl instance with mocked client"""
        self.mock_client = Mock()
        self.mock_client.is_ad5x = True
        self.job_control = JobControl(self.mock_client)

    def test_validate_valid_single_mapping(self):
        """Test validation passes with one valid mapping"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
        ]
        assert self.job_control._validate_material_mappings(mappings) is True

    def test_validate_valid_multiple_mappings(self):
        """Test validation passes with multiple valid mappings (up to 4)"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=i,
                slot_id=i + 1,
                material_name=f"Material{i}",
                tool_material_color="#FF0000",
                slot_material_color="#00FF00"
            )
            for i in range(4)
        ]
        assert self.job_control._validate_material_mappings(mappings) is True

    def test_validate_rejects_empty_array(self):
        """Test validation rejects empty material mappings array"""
        assert self.job_control._validate_material_mappings([]) is False

    def test_validate_rejects_too_many_mappings(self):
        """Test validation rejects more than 4 mappings"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
            for _ in range(5)
        ]
        assert self.job_control._validate_material_mappings(mappings) is False

    def test_validate_rejects_invalid_tool_id_negative(self):
        """Test Pydantic validation rejects toolId < 0"""
        # Pydantic should reject this at creation time
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=-1,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

    def test_validate_rejects_invalid_tool_id_too_high(self):
        """Test Pydantic validation rejects toolId > 3"""
        # Pydantic should reject this at creation time
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=4,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

    def test_validate_rejects_invalid_slot_id_zero(self):
        """Test Pydantic validation rejects slotId < 1"""
        # Pydantic should reject this at creation time
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=0,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

    def test_validate_rejects_invalid_slot_id_too_high(self):
        """Test Pydantic validation rejects slotId > 4"""
        # Pydantic should reject this at creation time
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=5,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )

    def test_validate_rejects_empty_material_name(self):
        """Test validation rejects empty materialName"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
        ]
        assert self.job_control._validate_material_mappings(mappings) is False

    def test_validate_rejects_whitespace_material_name(self):
        """Test validation rejects whitespace-only materialName"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="   ",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
        ]
        assert self.job_control._validate_material_mappings(mappings) is False

    def test_validate_rejects_invalid_tool_color_format(self):
        """Test validation rejects invalid toolMaterialColor format"""
        invalid_colors = [
            "FFFFFF",  # Missing #
            "#FFF",  # Too short
            "#GGGGGG",  # Invalid hex chars
            "#12345",  # Too short
            "#1234567",  # Too long
            "red",  # Color name not allowed
        ]

        for color in invalid_colors:
            mappings = [
                AD5XMaterialMapping(
                    tool_id=0,
                    slot_id=1,
                    material_name="PLA",
                    tool_material_color=color,
                    slot_material_color="#000000"
                )
            ]
            assert self.job_control._validate_material_mappings(mappings) is False, \
                f"Should reject tool color: {color}"

    def test_validate_rejects_invalid_slot_color_format(self):
        """Test validation rejects invalid slotMaterialColor format"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="INVALID"
            )
        ]
        assert self.job_control._validate_material_mappings(mappings) is False

    def test_validate_accepts_valid_color_formats(self):
        """Test validation accepts various valid hex color formats"""
        valid_colors = [
            "#000000",  # Black
            "#FFFFFF",  # White
            "#ff0000",  # Red (lowercase)
            "#00FF00",  # Green (mixed case)
            "#0000Ff",  # Blue (mixed case)
            "#AbCdEf",  # Mixed case hex
        ]

        for color in valid_colors:
            mappings = [
                AD5XMaterialMapping(
                    tool_id=0,
                    slot_id=1,
                    material_name="PLA",
                    tool_material_color=color,
                    slot_material_color="#000000"
                )
            ]
            assert self.job_control._validate_material_mappings(mappings) is True, \
                f"Should accept color: {color}"


class TestBase64Encoding:
    """Tests for _encode_material_mappings_to_base64() method"""

    def setup_method(self):
        """Create a JobControl instance with mocked client"""
        self.mock_client = Mock()
        self.mock_client.is_ad5x = True
        self.job_control = JobControl(self.mock_client)

    def test_encode_single_mapping(self):
        """Test base64 encoding of single material mapping"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
        ]

        result = self.job_control._encode_material_mappings_to_base64(mappings)

        # Verify it's valid base64
        decoded = base64.b64decode(result).decode('utf-8')
        data = json.loads(decoded)

        assert len(data) == 1
        assert data[0]["toolId"] == 0
        assert data[0]["slotId"] == 1
        assert data[0]["materialName"] == "PLA"
        assert data[0]["toolMaterialColor"] == "#FFFFFF"
        assert data[0]["slotMaterialColor"] == "#000000"

    def test_encode_multiple_mappings(self):
        """Test base64 encoding of multiple material mappings"""
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

        result = self.job_control._encode_material_mappings_to_base64(mappings)

        # Verify it's valid base64 and decodes correctly
        decoded = base64.b64decode(result).decode('utf-8')
        data = json.loads(decoded)

        assert len(data) == 3
        for i, item in enumerate(data):
            assert item["toolId"] == i
            assert item["slotId"] == i + 1
            assert item["materialName"] == f"Material{i}"

    def test_encode_produces_valid_base64(self):
        """Test that encoding produces valid base64 string"""
        mappings = [
            AD5XMaterialMapping(
                tool_id=0,
                slot_id=1,
                material_name="PLA",
                tool_material_color="#FFFFFF",
                slot_material_color="#000000"
            )
        ]

        result = self.job_control._encode_material_mappings_to_base64(mappings)

        # Should not raise exception
        try:
            base64.b64decode(result)
            is_valid = True
        except Exception:
            is_valid = False

        assert is_valid is True


class TestAD5XPrinterValidation:
    """Tests for _validate_ad5x_printer() method"""

    def test_validate_passes_for_ad5x_printer(self):
        """Test validation passes when printer is AD5X"""
        mock_client = Mock()
        mock_client.is_ad5x = True
        job_control = JobControl(mock_client)

        assert job_control._validate_ad5x_printer() is True

    def test_validate_fails_for_non_ad5x_printer(self):
        """Test validation fails when printer is not AD5X"""
        mock_client = Mock()
        mock_client.is_ad5x = False
        job_control = JobControl(mock_client)

        assert job_control._validate_ad5x_printer() is False
