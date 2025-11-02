# FlashForge Python API - Test Coverage Specification

**Version**: 1.0
**Date**: 2025-11-02
**Current Status**: 130 tests (100% passing), ~35-40% coverage
**Target Status**: ~195-200 tests (100% passing), ~75-80% coverage

---

## Executive Summary

This document outlines a comprehensive test suite expansion plan to achieve production-ready coverage for the FlashForge Python API. The API supports full automation of FlashForge 3D printers (AD5X, 5M Pro, 5M, and related models).

**Current Strengths:**
- ✅ Excellent AD5X multi-color feature coverage (57 tests)
- ✅ Robust discovery module testing (18 tests)
- ✅ Comprehensive utility class testing (32 tests)
- ✅ TCP parser testing for common scenarios (23 tests)

**Critical Gaps:**
- ❌ Control operations (LEDs, fans, camera, filtration) - 0% coverage
- ❌ Job control operations (pause/resume/cancel, file upload) - ~15% coverage
- ❌ Files module (file listing, thumbnails) - 0% coverage
- ❌ TCP client operations (socket management, keep-alive) - 0% coverage
- ❌ Main client initialization and lifecycle - 0% coverage
- ❌ Temperature control operations - 0% coverage

---

## Phase 1: Core API Tests (CRITICAL)

### 1.1 Main Client Tests (`tests/test_client.py`)

**Purpose**: Test the primary `FlashForgeClient` class that orchestrates all API operations.

**Location**: `flashforge/client.py`

#### Test Cases (8 tests):

```python
class TestFlashForgeClient:
    """Tests for the main FlashForgeClient class."""

    # Initialization & Connection
    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful client initialization with valid credentials."""
        # Mock HTTP and TCP responses
        # Verify initialize() returns True
        # Verify printer details are cached

    @pytest.mark.asyncio
    async def test_initialize_connection_failure(self):
        """Test initialization fails gracefully with invalid credentials."""
        # Mock connection failure
        # Verify initialize() returns False
        # Verify no cached details

    @pytest.mark.asyncio
    async def test_verify_connection_http_api_fails(self):
        """Test verify_connection when HTTP API is unreachable."""
        # Mock HTTP failure, TCP success
        # Verify returns False

    @pytest.mark.asyncio
    async def test_verify_connection_tcp_api_fails(self):
        """Test verify_connection when TCP API is unreachable."""
        # Mock HTTP success, TCP failure
        # Verify returns False

    # Detail Caching
    def test_cache_details_all_fields_ad5x(self):
        """Test caching printer details for AD5X printer."""
        # Create FFMachineInfo with AD5X fields
        # Call cache_details()
        # Verify all properties set (is_ad5x, is_pro, firmware_version, etc.)

    def test_cache_details_all_fields_5m_pro(self):
        """Test caching printer details for 5M Pro printer."""
        # Create FFMachineInfo with 5M Pro fields
        # Verify is_ad5x=False, is_pro=True

    # Context Manager
    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self):
        """Test async context manager properly initializes and cleans up."""
        # Use async with FlashForgeClient()
        # Verify __aenter__ calls initialize()
        # Verify __aexit__ calls dispose()
        # Check cleanup even on exception

    # HTTP Client State
    def test_http_client_busy_state_management(self):
        """Test HTTP client busy flag and release mechanism."""
        # Set busy state
        # Verify is_http_client_busy() returns True
        # Call release_http_client()
        # Verify is_http_client_busy() returns False
```

**Mocking Strategy:**
- Mock `aiohttp.ClientSession` for HTTP requests
- Mock `FlashForgeTcpClient` for TCP operations
- Use `unittest.mock.patch` for HTTP/TCP clients

**Live Integration Test:**
```python
@skip_if_no_printer("Requires AD5X or 5M Pro")
@pytest.mark.asyncio
async def test_initialize_live_ad5x(self):
    """Test initialization with real AD5X hardware."""
    config = get_test_printer_config()
    async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
        assert await client.initialize()
        assert client.is_ad5x == True
        assert client.printer_name != ""
```

---

### 1.2 Job Control Tests (`tests/test_job_control.py`)

**Purpose**: Test print job control operations (pause, resume, cancel, upload, start).

**Location**: `flashforge/api/controls/job_control.py`

#### Test Cases (10 tests):

```python
class TestJobControlOperations:
    """Tests for job control operations (non-AD5X)."""

    # Pause/Resume/Cancel
    @pytest.mark.asyncio
    async def test_pause_print_job_success(self):
        """Test pausing an active print job."""
        # Mock HTTP request to /print endpoint with action=pause
        # Verify correct payload
        # Verify returns True on success

    @pytest.mark.asyncio
    async def test_pause_print_job_when_idle(self):
        """Test pausing when no job is running."""
        # Mock printer status as idle
        # Verify appropriate error handling

    @pytest.mark.asyncio
    async def test_resume_print_job_success(self):
        """Test resuming a paused print job."""
        # Mock HTTP request with action=resume

    @pytest.mark.asyncio
    async def test_cancel_print_job_success(self):
        """Test canceling an active print job."""
        # Mock HTTP request with action=cancel

    # File Upload (Non-AD5X)
    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        """Test uploading a file to non-AD5X printer."""
        # Mock multipart form data upload
        # Verify file content and metadata
        # Test with test G-code file

    @pytest.mark.asyncio
    async def test_upload_file_not_found(self):
        """Test upload with non-existent file."""
        # Verify FileNotFoundError raised

    # Print Local File
    @pytest.mark.asyncio
    async def test_print_local_file_new_firmware(self):
        """Test starting print with firmware >= 3.1.3."""
        # Mock firmware version 3.1.3+
        # Mock HTTP request with new payload format
        # Verify uses {"printFileName": "file.gcode"}

    @pytest.mark.asyncio
    async def test_print_local_file_old_firmware(self):
        """Test starting print with firmware < 3.1.3."""
        # Mock firmware version 3.1.2
        # Verify uses {"fileName": "file.gcode"}

    # Firmware Version Detection
    def test_is_new_firmware_version_true(self):
        """Test firmware version comparison returns True for >= 3.1.3."""
        # Test versions: 3.1.3, 3.1.4, 3.2.0, 4.0.0

    def test_is_new_firmware_version_false(self):
        """Test firmware version comparison returns False for < 3.1.3."""
        # Test versions: 3.1.2, 3.1.1, 3.0.0, 2.9.0
```

**Key Validation Points:**
- Correct HTTP endpoint (`/print`)
- Proper payload structure for firmware versions
- Multipart form data encoding
- Error handling for file operations

**Live Integration Test:**
```python
@skip_if_no_printer("Requires printer for upload test")
@pytest.mark.asyncio
async def test_upload_small_test_file_live(self):
    """Test uploading a small test G-code file (no print start)."""
    # Create minimal valid G-code file (10 lines)
    # Upload to printer
    # Verify file appears in file list
    # Clean up: delete test file
```

---

### 1.3 Control Operations Tests (`tests/test_control.py`)

**Purpose**: Test printer control operations (LEDs, fans, camera, filtration, movement).

**Location**: `flashforge/api/controls/control.py`

#### Test Cases (7 tests):

```python
class TestControlOperations:
    """Tests for printer control operations."""

    # LED Control
    @pytest.mark.asyncio
    async def test_set_led_on_with_led_control_enabled(self):
        """Test turning LEDs on when printer supports LED control."""
        # Mock has_led_control=True
        # Mock HTTP POST to /control with {led: 1}
        # Verify success

    @pytest.mark.asyncio
    async def test_set_led_off(self):
        """Test turning LEDs off."""
        # Mock HTTP POST with {led: 0}

    # Filtration Control (5M Pro specific)
    @pytest.mark.asyncio
    async def test_set_external_filtration_on(self):
        """Test enabling external filtration (5M Pro feature)."""
        # Mock HTTP POST to /control with {externalFanStatus: 'open'}

    @pytest.mark.asyncio
    async def test_set_filtration_off(self):
        """Test disabling all filtration."""
        # Mock HTTP POST with {externalFanStatus: 'close', internalFanStatus: 'close'}

    # Fan Control with Safety Checks
    @pytest.mark.asyncio
    async def test_set_cooling_fan_speed_normal(self):
        """Test setting cooling fan speed during normal print."""
        # Mock current layer > 3
        # Mock HTTP POST with {coolingFanSpeed: 80}

    @pytest.mark.asyncio
    async def test_set_cooling_fan_speed_early_layer_protection(self):
        """Test cooling fan is restricted during early layers (safety feature)."""
        # Mock current layer <= 3
        # Attempt to set high speed
        # Verify speed is clamped or request is blocked

    # Homing
    @pytest.mark.asyncio
    async def test_home_axes_all(self):
        """Test homing all axes."""
        # Mock HTTP POST to /control with {commandText: 'G28'}
```

**Important Safety Features to Test:**
- Early layer cooling fan protection (don't blow off prints)
- LED control only available on certain models
- Filtration controls only on 5M Pro
- Camera controls validation

---

## Phase 2: Files & TCP Client Tests (HIGH PRIORITY)

### 2.1 Files Module Tests (`tests/test_files.py`)

**Purpose**: Test file listing and thumbnail retrieval from printer storage.

**Location**: `flashforge/api/controls/files.py`

#### Test Cases (8 tests):

**Reference**: This mirrors TypeScript `Files.test.ts` structure.

```python
class TestFilesModule:
    """Tests for file listing and thumbnail operations."""

    # Recent File List - AD5X Format
    @pytest.mark.asyncio
    async def test_get_recent_file_list_ad5x_format(self):
        """Test parsing recent files from AD5X printer (gcodeListDetail format)."""
        # Mock HTTP response with gcodeListDetail containing:
        # - gcodeFileName
        # - printingTime
        # - gcodeToolCnt
        # - gcodeToolDatas (array with material info)
        # - useMatlStation
        # Verify returns List[FFGcodeFileEntry]
        # Verify material data properly parsed

    # Recent File List - Older Printer Format
    @pytest.mark.asyncio
    async def test_get_recent_file_list_old_printer_format(self):
        """Test parsing recent files from non-AD5X printer (gcodeList string array)."""
        # Mock HTTP response with gcodeList: ["file1.gcode", "file2.gcode"]
        # Verify falls back to string array parsing
        # Verify creates FFGcodeFileEntry objects with minimal data

    @pytest.mark.asyncio
    async def test_get_recent_file_list_empty(self):
        """Test handling empty file list."""
        # Mock response with empty gcodeList
        # Verify returns empty list (not None or error)

    @pytest.mark.asyncio
    async def test_get_recent_file_list_http_error(self):
        """Test handling HTTP error when fetching file list."""
        # Mock HTTP 500 error
        # Verify appropriate error handling

    # Local File List
    @pytest.mark.asyncio
    async def test_get_local_file_list_with_files(self):
        """Test getting local file list via TCP."""
        # Mock TCP response with file names
        # Verify returns List[str]

    @pytest.mark.asyncio
    async def test_get_local_file_list_empty(self):
        """Test handling empty local file list."""
        # Verify returns empty list

    # Thumbnails
    @pytest.mark.asyncio
    async def test_get_gcode_thumbnail_success(self):
        """Test retrieving G-code thumbnail image."""
        # Mock HTTP response with base64 image data
        # Verify returns decoded bytes
        # Verify is valid image data

    @pytest.mark.asyncio
    async def test_get_gcode_thumbnail_not_found(self):
        """Test handling missing thumbnail."""
        # Mock 404 or empty response
        # Verify returns None (not error)
```

**Live Integration Test:**
```python
@skip_if_no_printer()
@pytest.mark.asyncio
async def test_get_file_lists_live_both_printers(self):
    """Test getting file lists from both AD5X and 5M Pro."""
    # Connect to AD5X
    # Get recent files, verify FFGcodeFileEntry structure
    # Connect to 5M Pro
    # Get recent files, verify fallback parsing works
```

---

### 2.2 TCP Client Tests (`tests/test_tcp_client.py`)

**Purpose**: Test low-level TCP communication, socket management, and response parsing.

**Location**: `flashforge/tcp/tcp_client.py`

#### Test Cases (12 tests):

**Reference**: Mirrors TypeScript `FlashForgeTcpClient.test.ts`.

```python
class TestTcpClientFileListParsing:
    """Tests for TCP file list response parsing."""

    def test_parse_file_list_response_pro_format(self):
        """Test parsing file list from Pro printer (prefix format)."""
        # Mock response: "/[FLASH]/file1.gcode|[FLASH]/file2.gcode"
        # Verify removes [FLASH] prefix
        # Verify splits on |

    def test_parse_file_list_response_regular_format(self):
        """Test parsing file list from regular printer (no prefix)."""
        # Mock response: "/file1.gcode|/file2.gcode"
        # Verify parses correctly

    def test_parse_file_list_response_with_spaces(self):
        """Test parsing filenames containing spaces."""
        # Mock: "/My File Name.gcode|/Another File.gcode"

    def test_parse_file_list_response_with_special_chars(self):
        """Test parsing filenames with special characters."""
        # Mock: "/Résumé_Test.gcode|/文件.gcode|/File(1).gcode"

    def test_parse_file_list_response_empty(self):
        """Test parsing empty file list response."""
        # Mock: ""
        # Verify returns empty list

class TestTcpClientCommands:
    """Tests for TCP command operations."""

    @pytest.mark.asyncio
    async def test_send_command_async_success(self):
        """Test sending TCP command successfully."""
        # Mock socket connection
        # Send "M119" command
        # Mock response
        # Verify command sent with ~
        # Verify response received

    @pytest.mark.asyncio
    async def test_send_command_async_timeout(self):
        """Test TCP command timeout handling."""
        # Mock socket that doesn't respond
        # Verify timeout exception

    @pytest.mark.asyncio
    async def test_send_command_async_connection_lost(self):
        """Test handling connection loss during command."""
        # Mock socket disconnection
        # Verify reconnection attempt

class TestTcpClientKeepAlive:
    """Tests for TCP keep-alive mechanism."""

    @pytest.mark.asyncio
    async def test_start_keep_alive(self):
        """Test keep-alive starts periodic heartbeat."""
        # Start keep-alive
        # Verify M119 sent periodically

    @pytest.mark.asyncio
    async def test_stop_keep_alive(self):
        """Test keep-alive stops cleanly."""
        # Start keep-alive
        # Stop keep-alive
        # Verify no more heartbeats sent

    @pytest.mark.asyncio
    async def test_keep_alive_handles_disconnection(self):
        """Test keep-alive recovers from connection loss."""
        # Start keep-alive
        # Simulate connection loss
        # Verify reconnection and keep-alive continues
```

**Key Testing Points:**
- File list parsing handles both Pro and regular formats
- Special characters and unicode in filenames
- Socket reconnection logic
- Keep-alive mechanism reliability

---

## Phase 3: Temperature & Info Tests (MEDIUM PRIORITY)

### 3.1 Temperature Control Tests (`tests/test_temp_control.py`)

**Purpose**: Test temperature setting and monitoring operations.

**Location**: `flashforge/api/controls/temp_control.py`

#### Test Cases (5 tests):

```python
class TestTemperatureControl:
    """Tests for temperature control operations."""

    @pytest.mark.asyncio
    async def test_set_extruder_temp_success(self):
        """Test setting extruder temperature."""
        # Mock HTTP POST to /control
        # Payload: {extruderTemp: 220}
        # Verify success

    @pytest.mark.asyncio
    async def test_cancel_extruder_temp(self):
        """Test canceling extruder heating."""
        # Mock POST with {extruderTemp: 0}

    @pytest.mark.asyncio
    async def test_set_bed_temp_success(self):
        """Test setting bed temperature."""
        # Mock POST with {bedTemp: 60}

    @pytest.mark.asyncio
    async def test_wait_for_part_cool_threshold(self):
        """Test waiting for part to cool below threshold."""
        # Mock info.get() returning decreasing temperatures
        # Set threshold to 50°C
        # Verify loops until temp < 50
        # Verify timeout handling

    @pytest.mark.asyncio
    async def test_set_temp_out_of_range(self):
        """Test validation of temperature values."""
        # Attempt to set extruder to 999°C
        # Verify error or clamping
```

---

### 3.2 Info Module Tests (`tests/test_info.py`)

**Purpose**: Test printer status and information retrieval.

**Location**: `flashforge/api/controls/info.py`

#### Test Cases (5 tests):

```python
class TestInfoModule:
    """Tests for printer information retrieval."""

    @pytest.mark.asyncio
    async def test_get_info_success_ad5x(self):
        """Test getting printer info from AD5X."""
        # Mock HTTP response with AD5X fields
        # Verify FFMachineInfo returned
        # Verify AD5X-specific fields parsed (matl_station_info, etc.)

    @pytest.mark.asyncio
    async def test_get_info_success_5m_pro(self):
        """Test getting printer info from 5M Pro."""
        # Mock response for 5M Pro
        # Verify is_ad5x=False, is_pro=True

    @pytest.mark.asyncio
    async def test_is_printing_true(self):
        """Test is_printing() returns True when printing."""
        # Mock info with status="printing"
        # Verify is_printing() == True

    @pytest.mark.asyncio
    async def test_get_machine_state_ready(self):
        """Test get_machine_state() returns READY state."""
        # Mock info with machine_state=MachineState.READY

    @pytest.mark.asyncio
    async def test_get_detail_response_http_error(self):
        """Test handling HTTP error when fetching detail."""
        # Mock HTTP 500 error
        # Verify returns None (not crash)
```

---

## Phase 4: Additional Parsers & Error Handling

### 4.1 Additional Parser Tests (`tests/test_additional_parsers.py`)

**Purpose**: Test parsers not yet comprehensively covered.

**Locations**: `flashforge/tcp/parsers/`

#### Test Cases (6 tests):

```python
class TestLocationInfo:
    """Tests for LocationInfo parser."""

    def test_parse_valid_location_response(self):
        """Test parsing valid M114 (position) response."""
        # Mock: "X:100.00 Y:150.00 Z:10.50"
        # Verify LocationInfo object created
        # Verify x, y, z values correct

    def test_parse_invalid_location_response(self):
        """Test handling malformed location data."""
        # Verify returns None or default

class TestTempInfo:
    """Tests for TempInfo parser."""

    def test_parse_valid_temp_response(self):
        """Test parsing M105 (temperature) response."""
        # Mock: "T0:220/220 B:60/60"
        # Verify TempInfo object
        # Verify extruder and bed temps

    def test_parse_temp_response_cooling(self):
        """Test parsing when target temps are 0 (cooling)."""
        # Mock: "T0:50/0 B:30/0"

class TestPrinterInfo:
    """Tests for PrinterInfo parser."""

    def test_parse_printer_info_complete(self):
        """Test parsing complete printer info response."""
        # Mock full M115 response
        # Verify all fields parsed

    def test_parse_printer_info_minimal(self):
        """Test parsing minimal printer info."""
        # Mock response with only required fields
```

---

### 4.2 Network Error Handling Tests

**Purpose**: Add error handling tests to existing test files.

**Strategy**: Add these tests to the appropriate existing files.

#### Add to `tests/test_client.py` (3 tests):

```python
@pytest.mark.asyncio
async def test_initialize_connection_timeout(self):
    """Test initialization handles connection timeout gracefully."""
    # Mock asyncio.TimeoutError
    # Verify initialize() returns False
    # Verify error logged

@pytest.mark.asyncio
async def test_initialize_invalid_ip_address(self):
    """Test initialization with malformed IP address."""
    # IP: "999.999.999.999"
    # Verify error handling

@pytest.mark.asyncio
async def test_initialize_network_unreachable(self):
    """Test initialization when network is down."""
    # Mock OSError
```

#### Add to `tests/test_files.py` (3 tests):

```python
@pytest.mark.asyncio
async def test_get_recent_file_list_malformed_json(self):
    """Test handling malformed JSON response."""
    # Mock HTTP response with invalid JSON
    # Verify returns empty list or raises appropriate error

@pytest.mark.asyncio
async def test_get_recent_file_list_network_timeout(self):
    """Test handling network timeout during file list fetch."""
    # Mock asyncio.TimeoutError

@pytest.mark.asyncio
async def test_get_recent_file_list_connection_reset(self):
    """Test handling connection reset."""
    # Mock ConnectionResetError
```

#### Add to `tests/test_discovery.py` (3 tests):

```python
@pytest.mark.asyncio
async def test_discover_printers_network_interface_down(self):
    """Test discovery when network interface is unavailable."""
    # Mock no network interfaces
    # Verify returns empty list (not crash)

@pytest.mark.asyncio
async def test_discover_printers_broadcast_blocked(self):
    """Test discovery when broadcast packets are blocked by firewall."""
    # Mock permission denied on broadcast

@pytest.mark.asyncio
async def test_discover_printers_malformed_response(self):
    """Test handling corrupted discovery response packets."""
    # Mock response with invalid data
    # Verify skips malformed responses, continues discovery
```

---

## Phase 5: Live Integration for 5M Pro

### 5.1 5M Pro Live Integration Tests (`tests/test_5m_pro_live_integration.py`)

**Purpose**: Validate API works correctly with non-AD5X printer hardware.

**Prerequisites**:
- Update `tests/printer_config.py` with 5M Pro credentials
- Ensure 5M Pro is powered on and connected to network

#### Configuration Update (`tests/printer_config.py`):

```python
# Add these to printer_config.py:

# 5M Pro Configuration
PRINTER_5M_PRO_IP = "192.168.1.140"
PRINTER_5M_PRO_SERIAL = "SNMOMC9900728"
PRINTER_5M_PRO_CHECK_CODE = "your_check_code_here"
PRINTER_5M_PRO_NAME = "Adventurer 5M Pro"

def get_5m_pro_config() -> dict:
    """Returns the 5M Pro printer configuration."""
    return {
        "ip": PRINTER_5M_PRO_IP,
        "serial_number": PRINTER_5M_PRO_SERIAL,
        "check_code": PRINTER_5M_PRO_CHECK_CODE,
        "name": PRINTER_5M_PRO_NAME,
    }
```

#### Test Cases (5 tests):

```python
@pytest.mark.asyncio
@skip_if_no_printer("Requires 5M Pro printer")
class Test5MProLiveIntegration:
    """Live integration tests with 5M Pro hardware."""

    async def test_connect_and_get_status_5m_pro(self):
        """Test connecting to 5M Pro and retrieving status."""
        config = get_5m_pro_config()
        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()
            assert client.printer_name == "Adventurer 5M Pro"
            assert client.is_ad5x == False
            assert client.is_pro == True

            info = await client.info.get()
            assert info is not None
            assert info.is_ad5x == False
            assert info.has_matl_station is None  # Not AD5X, shouldn't have this

    async def test_get_file_list_5m_pro(self):
        """Test getting file list from 5M Pro (non-AD5X format)."""
        config = get_5m_pro_config()
        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # Get recent files - should use fallback parsing (string array)
            files = await client.files.get_recent_file_list()
            assert isinstance(files, list)
            # 5M Pro may have files, verify structure
            for file_entry in files:
                assert hasattr(file_entry, 'gcode_file_name')
                # Should NOT have AD5X-specific fields like gcode_tool_datas

    async def test_led_control_5m_pro(self):
        """Test LED control on 5M Pro (has built-in LEDs)."""
        config = get_5m_pro_config()
        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # 5M Pro has LED control
            # Turn LED on (don't actually test, just verify API doesn't error)
            # In real test: await client.control.set_led_on()
            # Verify no exceptions
            # Turn LED off: await client.control.set_led_off()
            pass  # Placeholder - implement when LED control tests exist

    async def test_filtration_control_5m_pro(self):
        """Test filtration control on 5M Pro (has external filtration)."""
        config = get_5m_pro_config()
        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # 5M Pro has external filtration
            # Test external filtration API doesn't error
            # await client.control.set_external_filtration_on()
            # await client.control.set_filtration_off()
            pass  # Placeholder

    async def test_job_control_validation_5m_pro(self):
        """Test job control validation works on 5M Pro."""
        config = get_5m_pro_config()
        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # Verify can't pause when not printing
            info = await client.info.get()
            if not info.is_printing():
                # Attempt pause should fail gracefully
                # result = await client.job_control.pause_print_job()
                # assert result == False
                pass
```

---

## Implementation Guidelines

### Testing Best Practices

#### 1. Mock Structure

Use consistent mocking patterns across all tests:

```python
from unittest.mock import Mock, AsyncMock, patch

# For HTTP requests:
@patch('aiohttp.ClientSession.post')
async def test_something(self, mock_post):
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"code": 0})
    mock_post.return_value.__aenter__.return_value = mock_response

# For TCP operations:
@patch('flashforge.tcp.tcp_client.FlashForgeTcpClient.send_command_async')
async def test_tcp_command(self, mock_send):
    mock_send.return_value = "ok\n"
```

#### 2. Test Data Fixtures

Create reusable test data fixtures:

```python
# tests/fixtures/printer_responses.py

AD5X_INFO_RESPONSE = {
    "code": 0,
    "data": {
        "name": "AD5X",
        "firmwareVersion": "1.1.7-1.0.2",
        "hasMatlStation": True,
        "matlStationInfo": {
            "currentLoadSlot": 1,
            "currentSlot": 1,
            "slotCnt": 4,
            "slotInfos": [
                {"slotId": 1, "hasFilament": True, "materialName": "PLA", "materialColor": "#FF0000"}
            ],
            "stateAction": 0,
            "stateStep": 0
        },
        # ... full response
    }
}

FIVE_M_PRO_INFO_RESPONSE = {
    "code": 0,
    "data": {
        "name": "Adventurer 5M Pro",
        "firmwareVersion": "3.2.0",
        # ... 5M Pro specific fields
    }
}

FILE_LIST_AD5X_RESPONSE = {
    "code": 0,
    "gcodeListDetail": [
        {
            "gcodeFileName": "test.3mf",
            "printingTime": 1000,
            "gcodeToolCnt": 2,
            "gcodeToolDatas": [
                {"toolId": 0, "slotId": 1, "materialName": "PLA", "materialColor": "#FF0000", "filamentWeight": 50.5}
            ],
            "useMatlStation": True
        }
    ]
}
```

#### 3. Error Testing Pattern

Consistent error testing approach:

```python
async def test_operation_http_error(self):
    """Test handling HTTP 500 error."""
    # Arrange
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")

    # Act & Assert
    with pytest.raises(Exception):  # Or specific exception
        await operation()

    # OR if should return None:
    result = await operation()
    assert result is None
```

#### 4. Live Test Pattern

Consistent live test structure:

```python
@skip_if_no_printer("Requires AD5X printer")
@pytest.mark.asyncio
async def test_feature_live(self):
    """Test feature with real hardware - describe what it does."""
    config = get_test_printer_config()

    async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
        # Initialize
        assert await client.initialize(), "Failed to connect to printer"

        # Test operation
        result = await client.some_operation()

        # Validate
        assert result is not None
        # ... more validations

        # Cleanup (if needed)
        # await client.cleanup_operation()
```

### Testing Checklist

Before considering a module "fully tested":

- [ ] All public methods have at least one test
- [ ] Success path tested
- [ ] Error paths tested (HTTP errors, network errors, invalid data)
- [ ] Edge cases tested (empty responses, boundary values)
- [ ] Live integration test exists (if hardware-dependent)
- [ ] Mocked tests don't make real network calls
- [ ] Tests are isolated (don't depend on order)
- [ ] Tests clean up after themselves
- [ ] Test names clearly describe what's being tested
- [ ] Docstrings explain test purpose and setup

---

## Test Execution Strategy

### Running Test Subsets

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests (mocked, fast)
pytest tests/ -v -m "not live"

# Run only live integration tests
pytest tests/ -v --tb=short -k "live"

# Run specific module
pytest tests/test_client.py -v

# Run with coverage report
pytest tests/ --cov=flashforge --cov-report=html

# Run AD5X tests only
pytest tests/ -k "ad5x" -v

# Run 5M Pro tests only
pytest tests/ -k "5m_pro" -v
```

### CI/CD Considerations

For continuous integration:

```yaml
# Example .github/workflows/test.yml structure

jobs:
  unit-tests:
    # Fast mocked tests - run on every commit
    - pytest tests/ -v --ignore=tests/test_*_live_integration.py

  integration-tests:
    # Live tests - run nightly or on demand
    # Requires hardware in CI environment
    - pytest tests/ -v -k "live"
```

---

## Expected Outcomes

### Coverage Metrics

**Current State (130 tests):**
```
Module                          Current    Target
────────────────────────────────────────────────────
flashforge/client.py            0%         90%
flashforge/api/controls/
  ├── control.py                0%         85%
  ├── job_control.py            15%        90%
  ├── files.py                  0%         85%
  ├── info.py                   10%        80%
  └── temp_control.py           0%         75%
flashforge/tcp/tcp_client.py    0%         80%
flashforge/tcp/parsers/
  ├── endstop_status.py         60%        85%
  ├── location_info.py          0%         75%
  ├── temp_info.py              0%         75%
  └── printer_info.py           10%        75%
flashforge/models/              95%        95% ✓
flashforge/discovery/           90%        90% ✓
flashforge/api/filament/        95%        95% ✓
────────────────────────────────────────────────────
OVERALL                         ~38%       ~78%
```

**After Implementation (~200 tests):**
- 18 new client tests → client.py: 90% coverage
- 10 new job control tests → job_control.py: 90% coverage
- 7 new control tests → control.py: 85% coverage
- 8 new files tests → files.py: 85% coverage
- 12 new TCP client tests → tcp_client.py: 80% coverage
- 5 new temp control tests → temp_control.py: 75% coverage
- 5 new info tests → info.py: 80% coverage
- 6 new parser tests → parsers: 80% avg
- 9 new error handling tests → error coverage: 70%
- 5 new 5M Pro integration tests → 5M Pro validation: 80%

### Test Execution Time

**Estimated test execution times:**

- Unit tests (mocked): ~5-8 seconds for 135 tests
- AD5X live integration: ~2-3 seconds for 16 tests
- 5M Pro live integration: ~2-3 seconds for 5 tests
- Discovery live test: ~10 seconds for 1 test
- New unit tests: ~8-10 seconds for 65 tests

**Total**:
- Full suite without live: ~15 seconds
- Full suite with live: ~30 seconds

### Confidence Level

After implementation:

- ✅ **Core API functionality**: 90% confidence (thoroughly tested)
- ✅ **AD5X features**: 95% confidence (already excellent)
- ✅ **5M Pro compatibility**: 85% confidence (validated with hardware)
- ✅ **Error handling**: 75% confidence (major scenarios covered)
- ✅ **Production readiness**: 80% confidence (comprehensive coverage)

---

## Maintenance & Updates

### When to Add New Tests

Add tests when:

1. **New features are implemented**
   - Write tests before or alongside feature code (TDD)
   - Ensure new code has >80% coverage

2. **Bugs are discovered**
   - Write regression test that reproduces bug
   - Fix bug
   - Verify test now passes

3. **API changes**
   - Update existing tests to match new behavior
   - Add tests for new parameters/responses

4. **New printer models**
   - Add live integration tests for new hardware
   - Test model-specific features

### Test Review Checklist

When reviewing tests:

- [ ] Tests are independent (can run in any order)
- [ ] Tests use appropriate fixtures/mocking
- [ ] Test names follow convention: `test_<method>_<scenario>`
- [ ] Live tests use `@skip_if_no_printer()` decorator
- [ ] Error cases are tested
- [ ] Edge cases are covered
- [ ] Tests have clear docstrings
- [ ] No hardcoded credentials (use config)
- [ ] Tests clean up resources (files, connections)

---

## Priority Summary

### Phase 1 (CRITICAL) - Do This First
- ✅ Main client initialization and lifecycle
- ✅ Job control operations (pause/resume/cancel)
- ✅ Control operations (LED, fans, filtration)
- **Impact**: Tests core API functionality, blocks production use
- **Effort**: ~25 tests, 3-4 hours
- **Coverage gain**: +20%

### Phase 2 (HIGH) - Do This Second
- ✅ Files module (file listing, thumbnails)
- ✅ TCP client operations (socket management)
- **Impact**: Validates communication layer, ensures reliability
- **Effort**: ~20 tests, 3-4 hours
- **Coverage gain**: +18%

### Phase 3 (MEDIUM) - Do When Ready
- ✅ Temperature control operations
- ✅ Info module comprehensive tests
- **Impact**: Completes feature coverage
- **Effort**: ~10 tests, 1-2 hours
- **Coverage gain**: +8%

### Phase 4 (ONGOING) - Sprinkle Throughout
- ✅ Error handling in all modules
- ✅ Additional parser tests
- **Impact**: Improves robustness and edge case handling
- **Effort**: ~15 tests, 2-3 hours
- **Coverage gain**: +10%

### Phase 5 (VALIDATION) - Hardware Testing
- ✅ 5M Pro live integration tests
- **Impact**: Validates backward compatibility
- **Effort**: ~5 tests, 1 hour (requires hardware access)
- **Coverage gain**: +5% (validation coverage)

---

## Conclusion

This specification provides a complete roadmap for achieving production-ready test coverage for the FlashForge Python API. Implementation of all phases will result in:

- **~200 total tests** (up from 130)
- **~78% code coverage** (up from ~38%)
- **Full automation support** validated
- **Both printer models tested** (AD5X and 5M Pro)
- **Robust error handling** verified
- **TypeScript feature parity** achieved

The test suite will provide confidence for:
- Production deployments
- API refactoring
- Adding new features
- Supporting new printer models
- Catching regressions early

**Recommended Timeline**:
- Phase 1: Week 1 (critical core tests)
- Phase 2: Week 2 (high priority communication tests)
- Phase 4: Week 2-3 (error handling sprinkled in)
- Phase 5: Week 3 (hardware validation)
- Phase 3: Week 4 (medium priority features, can be deferred)

Total estimated effort: **12-15 hours** of focused implementation time.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-02
**Next Review**: After Phase 1 completion
