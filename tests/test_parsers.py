"""
Tests for FlashForge TCP parsers functionality.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to sys.path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flashforge.tcp.parsers import (
    EndstopStatus, MachineStatus, MoveMode, Status, Endstop,
    PrintStatus, ThumbnailInfo
)


class TestEndstopStatus:
    """Test cases for EndstopStatus parser."""
    
    def test_endstop_parsing(self):
        """Test parsing endstop data."""
        data = "Endstop X-max:0 Y-max:0 Z-min:1"
        endstop = Endstop(data)
        
        assert endstop.x_max == 0
        assert endstop.y_max == 0
        assert endstop.z_min == 1
    
    def test_endstop_parsing_invalid(self):
        """Test parsing endstop data with invalid format."""
        data = "Invalid endstop data"
        endstop = Endstop(data)
        
        # Should return -1 for unparseable values
        assert endstop.x_max == -1
        assert endstop.y_max == -1
        assert endstop.z_min == -1
    
    def test_status_parsing(self):
        """Test parsing status flags."""
        data = "Status S:1 L:0 J:2 F:3"
        status = Status(data)
        
        assert status.s == 1
        assert status.l == 0
        assert status.j == 2
        assert status.f == 3
    
    def test_status_parsing_partial(self):
        """Test parsing status with missing flags."""
        data = "Status S:5 J:10"
        status = Status(data)
        
        assert status.s == 5
        assert status.l == -1  # Missing, should be -1
        assert status.j == 10
        assert status.f == -1  # Missing, should be -1
    
    def test_endstop_status_full_parsing(self):
        """Test parsing a complete endstop status response."""
        replay = """~M119
Endstop X-max:0 Y-max:0 Z-min:1
MachineStatus: READY
MoveMode: READY
Status S:0 L:0 J:0 F:0
LED: 1
CurrentFile: test_print.gx"""
        
        endstop_status = EndstopStatus()
        result = endstop_status.from_replay(replay)
        
        assert result is not None
        assert endstop_status.endstop is not None
        assert endstop_status.endstop.z_min == 1
        assert endstop_status.machine_status == MachineStatus.READY
        assert endstop_status.move_mode == MoveMode.READY
        assert endstop_status.led_enabled is True
        assert endstop_status.current_file == "test_print.gx"
    
    def test_endstop_status_printing(self):
        """Test parsing endstop status when printing."""
        replay = """~M119
Endstop X-max:0 Y-max:0 Z-min:0
MachineStatus: BUILDING_FROM_SD
MoveMode: MOVING
Status S:1 L:1 J:0 F:1
LED: 1
CurrentFile: large_print.gx"""
        
        endstop_status = EndstopStatus()
        result = endstop_status.from_replay(replay)
        
        assert result is not None
        assert endstop_status.machine_status == MachineStatus.BUILDING_FROM_SD
        assert endstop_status.move_mode == MoveMode.MOVING
        assert endstop_status.is_printing() is True
        assert endstop_status.is_ready() is False
        assert endstop_status.current_file == "large_print.gx"
    
    def test_endstop_status_paused(self):
        """Test parsing endstop status when paused."""
        replay = """~M119
Endstop X-max:0 Y-max:0 Z-min:0
MachineStatus: PAUSED
MoveMode: PAUSED
Status S:0 L:0 J:1 F:0
LED: 1
CurrentFile: paused_print.gx"""
        
        endstop_status = EndstopStatus()
        result = endstop_status.from_replay(replay)
        
        assert result is not None
        assert endstop_status.machine_status == MachineStatus.PAUSED
        assert endstop_status.move_mode == MoveMode.PAUSED
        assert endstop_status.is_paused() is True
        assert endstop_status.is_printing() is False
    
    def test_endstop_status_complete(self):
        """Test parsing endstop status when print is complete."""
        replay = """~M119
Endstop X-max:0 Y-max:0 Z-min:1
MachineStatus: BUILDING_COMPLETED
MoveMode: READY
Status S:0 L:0 J:0 F:1
LED: 0
CurrentFile: completed_print.gx"""
        
        endstop_status = EndstopStatus()
        result = endstop_status.from_replay(replay)
        
        assert result is not None
        assert endstop_status.machine_status == MachineStatus.BUILDING_COMPLETED
        assert endstop_status.is_print_complete() is True
        assert endstop_status.led_enabled is False
    
    def test_endstop_status_invalid_replay(self):
        """Test parsing with invalid replay data."""
        endstop_status = EndstopStatus()
        
        # Test with None
        assert endstop_status.from_replay(None) is None
        
        # Test with empty string
        assert endstop_status.from_replay("") is None
        
        # Test with malformed data
        assert endstop_status.from_replay("Invalid data") is None
    
    def test_endstop_status_string_representations(self):
        """Test string representations of EndstopStatus."""
        replay = """~M119
Endstop X-max:0 Y-max:0 Z-min:1
MachineStatus: READY
MoveMode: READY
Status S:0 L:0 J:0 F:0
LED: 1
CurrentFile: test.gx"""
        
        endstop_status = EndstopStatus()
        endstop_status.from_replay(replay)
        
        str_repr = str(endstop_status)
        assert "READY" in str_repr
        assert "test.gx" in str_repr
        
        repr_str = repr(endstop_status)
        assert "EndstopStatus" in repr_str


class TestPrintStatus:
    """Test cases for PrintStatus parser."""
    
    def test_print_status_parsing(self):
        """Test parsing a complete print status response."""
        replay = """~M27
SD printing byte 12345/67890
Layer: 25/100"""
        
        print_status = PrintStatus()
        result = print_status.from_replay(replay)
        
        assert result is not None
        assert print_status.sd_current == "12345"
        assert print_status.sd_total == "67890"
        assert print_status.layer_current == "25"
        assert print_status.layer_total == "100"
    
    def test_print_status_progress_calculation(self):
        """Test print progress percentage calculations."""
        replay = """~M27
SD printing byte 50000/100000
Layer: 40/80"""
        
        print_status = PrintStatus()
        print_status.from_replay(replay)
        
        # Test layer progress
        layer_percent = print_status.get_print_percent()
        assert layer_percent == 50  # 40/80 = 50%
        
        # Test SD progress
        sd_percent = print_status.get_sd_percent()
        assert sd_percent == 50  # 50000/100000 = 50%
        
        # Test progress strings
        assert print_status.get_layer_progress() == "40/80"
        assert print_status.get_sd_progress() == "50000/100000"
    
    def test_print_status_edge_cases(self):
        """Test print status with edge cases."""
        # Test with zero total layers
        replay_zero = """~M27
SD printing byte 1000/10000
Layer: 5/0"""
        
        print_status = PrintStatus()
        print_status.from_replay(replay_zero)
        
        layer_percent = print_status.get_print_percent()
        assert layer_percent != layer_percent  # Should be NaN
        
        # Test completion check
        replay_complete = """~M27
SD printing byte 100000/100000
Layer: 50/50"""
        
        print_status = PrintStatus()
        print_status.from_replay(replay_complete)
        
        assert print_status.is_complete() is True
        assert print_status.get_print_percent() == 100
    
    def test_print_status_invalid_data(self):
        """Test print status with invalid data."""
        print_status = PrintStatus()
        
        # Test with None
        assert print_status.from_replay(None) is None
        
        # Test with malformed SD progress
        bad_replay = """~M27
SD printing byte invalid_format
Layer: 10/20"""
        
        assert print_status.from_replay(bad_replay) is None
        
        # Test with malformed layer progress
        bad_replay2 = """~M27
SD printing byte 1000/2000
Layer: bad_format"""
        
        assert print_status.from_replay(bad_replay2) is None
    
    def test_print_status_string_representations(self):
        """Test string representations of PrintStatus."""
        replay = """~M27
SD printing byte 30000/60000
Layer: 15/30"""
        
        print_status = PrintStatus()
        print_status.from_replay(replay)
        
        str_repr = str(print_status)
        assert "15/30" in str_repr
        assert "50%" in str_repr  # Should show 50% for both layer and SD
        
        repr_str = repr(print_status)
        assert "PrintStatus" in repr_str
        assert "30000" in repr_str


class TestThumbnailInfo:
    """Test cases for ThumbnailInfo parser."""
    
    def test_thumbnail_info_creation(self):
        """Test creating a ThumbnailInfo instance."""
        thumbnail = ThumbnailInfo()
        assert thumbnail.get_image_data() is None
        assert thumbnail.get_file_name() is None
        assert thumbnail.has_image_data() is False
    
    def test_thumbnail_info_valid_png(self):
        """Test parsing a response with valid PNG data."""
        # Create a minimal PNG signature
        png_signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        png_data = png_signature + b'fake_png_data_for_testing'
        
        # Simulate printer response with "ok" followed by binary data
        response = "ok" + png_data.decode('latin1')
        
        thumbnail = ThumbnailInfo()
        result = thumbnail.from_replay(response, "test_file.gx")
        
        assert result is not None
        assert thumbnail.has_image_data() is True
        assert thumbnail.get_file_name() == "test_file.gx"
        
        # Check that image data is available
        image_data = thumbnail.get_image_data()
        assert image_data is not None
        assert len(image_data) > 0
    
    def test_thumbnail_info_no_ok(self):
        """Test parsing response without 'ok' delimiter."""
        response = "no_ok_delimiter_here"
        
        thumbnail = ThumbnailInfo()
        result = thumbnail.from_replay(response, "test.gx")
        
        assert result is None
    
    def test_thumbnail_info_no_png_signature(self):
        """Test parsing response without PNG signature."""
        response = "ok" + "no_png_signature_data"
        
        thumbnail = ThumbnailInfo()
        result = thumbnail.from_replay(response, "test.gx")
        
        assert result is None
    
    def test_thumbnail_info_base64_conversion(self):
        """Test Base64 data URL conversion."""
        # Create mock PNG data
        png_signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        png_data = png_signature + b'test_data'
        response = "ok" + png_data.decode('latin1')
        
        thumbnail = ThumbnailInfo()
        thumbnail.from_replay(response, "test.gx")
        
        # Test Base64 data URL
        data_url = thumbnail.to_base64_data_url()
        assert data_url is not None
        assert data_url.startswith("data:image/png;base64,")
        
        # Test raw Base64
        base64_data = thumbnail.get_image_data()
        assert base64_data is not None
        assert len(base64_data) > 0
    
    def test_thumbnail_info_save_file(self, tmp_path):
        """Test saving thumbnail to file."""
        # Create mock PNG data
        png_signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        # Add minimal PNG header for size detection
        png_header = png_signature + b'\x00\x00\x00\x0D' + b'IHDR' + b'\x00\x00\x00\x10\x00\x00\x00\x10'
        png_data = png_header + b'test_png_data'
        response = "ok" + png_data.decode('latin1')
        
        thumbnail = ThumbnailInfo()
        thumbnail.from_replay(response, "test_file.gx")
        
        # Test saving to specific path
        save_path = tmp_path / "test_thumbnail.png"
        success = thumbnail.save_to_file_sync(str(save_path))
        
        assert success is True
        assert save_path.exists()
        assert save_path.read_bytes() == png_data
        
        # Test auto-generated filename
        thumbnail2 = ThumbnailInfo()
        thumbnail2.from_replay(response, "another_file.gx")
        
        # Change to temp directory for auto-generated filename
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            success2 = thumbnail2.save_to_file_sync()
            assert success2 is True
            assert (tmp_path / "another_file.png").exists()
        finally:
            os.chdir(old_cwd)
    
    def test_thumbnail_info_image_size(self):
        """Test getting image dimensions."""
        # Create PNG with specific dimensions (16x16)
        png_signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        png_header = (png_signature + 
                     b'\x00\x00\x00\x0D' +  # IHDR chunk length
                     b'IHDR' +                # IHDR chunk type
                     b'\x00\x00\x00\x10' +  # Width: 16
                     b'\x00\x00\x00\x10' +  # Height: 16  
                     b'\x08\x02\x00\x00\x00')  # Bit depth, color type, etc.
        
        response = "ok" + png_header.decode('latin1')
        
        thumbnail = ThumbnailInfo()
        thumbnail.from_replay(response, "test.gx")
        
        width, height = thumbnail.get_image_size()
        assert width == 16
        assert height == 16
    
    def test_thumbnail_info_string_representations(self):
        """Test string representations of ThumbnailInfo."""
        # Test empty thumbnail
        thumbnail = ThumbnailInfo()
        str_repr = str(thumbnail)
        assert "no data" in str_repr
        
        # Test thumbnail with data
        png_data = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' + b'test'
        response = "ok" + png_data.decode('latin1')
        
        thumbnail.from_replay(response, "test.gx")
        
        str_repr = str(thumbnail)
        assert "test.gx" in str_repr
        assert "bytes" in str_repr
        
        repr_str = repr(thumbnail)
        assert "ThumbnailInfo" in repr_str
        assert "has_data=True" in repr_str


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
