# API Reference

This document provides a comprehensive reference for the FlashForge Python API, including all classes, methods, and data models.

## Core Client

### `flashforge.FlashForgeClient`

Main client for interacting with a FlashForge 3D printer. Orchestrates both HTTP and TCP communication layers.

#### Constructor

```python
FlashForgeClient(ip_address: str, serial_number: str, check_code: str)
```

**Parameters:**
- `ip_address` (str): IP address of the printer
- `serial_number` (str): Serial number of the printer (required for HTTP API)
- `check_code` (str): Authentication check code

#### Methods

**Connection Management:**

- `async initialize() -> bool`  
  Initializes connection and verifies printer. Returns `True` if successful.

- `async init_control() -> bool`  
  Initializes control interface (required for some operations). Returns `True` if successful.

- `async dispose() -> None`  
  Cleans up resources, stops keep-alive, closes connections.

**Status & Information:**

- `async get_printer_status() -> Optional[FFMachineInfo]`  
  Gets current printer status and information.

- `async get_temperatures() -> Optional[TempInfo]`  
  Gets current temperature readings from TCP client.

**Control Operations:**

- `async home_all_axes() -> bool`  
  Homes all axes (X, Y, Z).

- `async emergency_stop() -> bool`  
  Performs emergency stop.

- `async pause_print() -> bool`  
  Pauses current print job.

- `async resume_print() -> bool`  
  Resumes paused print job.

- `async cancel_print() -> bool`  
  Cancels current print job.

#### Properties

- `is_ad5x: bool` - True if printer is AD5X model
- `printer_name: str` - Cached printer name
- `is_pro: bool` - True if Pro model
- `firmware_version: str` - Firmware version string
- `mac_address: str` - MAC address
- `led_control: bool` - True if LED control available
- `filtration_control: bool` - True if filtration control available

#### Control Module Accessors

- `control: Control` - General machine control
- `job_control: JobControl` - Print job management
- `files: Files` - File operations
- `info: Info` - Information retrieval
- `temp_control: TempControl` - Temperature management
- `tcp_client: FlashForgeTcpClient` - Low-level TCP client

#### Context Manager

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    # Use client...
# Automatic cleanup
```

---

## Discovery

### `flashforge.FlashForgePrinterDiscovery`

Handles UDP-based printer discovery on the local network.

#### Methods

- `async discover_printers_async(timeout_ms: int = 3000, idle_timeout_ms: int = 1000, max_retries: int = 3) -> List[FlashForgePrinter]`  
  Discovers printers on the network. Returns list of discovered printers.

**Parameters:**
- `timeout_ms` (int): Total discovery timeout in milliseconds (default: 3000)
- `idle_timeout_ms` (int): Idle timeout between responses (default: 1000)
- `max_retries` (int): Maximum retry attempts (default: 3)

### `flashforge.FlashForgePrinter`

Data class representing a discovered printer.

**Properties:**
- `name: str` - Printer name
- `serial_number: str` - Serial number
- `ip_address: str` - IP address

---

## Control Modules

### `flashforge.api.controls.Control`

General machine control operations.

#### Homing

- `async home_axes() -> bool`  
  Homes X, Y, and Z axes.

- `async home_axes_rapid() -> bool`  
  Performs rapid homing of all axes.

#### LED Control (HTTP)

- `async set_led_on() -> bool`  
  Turns on LED lights (requires `led_control` capability).

- `async set_led_off() -> bool`  
  Turns off LED lights.

**Note:** For printers with aftermarket LEDs or when the `led_control` capability flag is incorrectly `False`, you can use the TCP-based LED control methods via `client.tcp_client.led_on()` and `client.tcp_client.led_off()`. See [Advanced Usage](advanced.md#dual-mode-led-control) for examples.

#### Filtration Control

- `async set_external_filtration_on() -> bool`  
  Turns on external filtration system.

- `async set_internal_filtration_on() -> bool`  
  Turns on internal filtration system.

- `async set_filtration_off() -> bool`  
  Turns off all filtration systems.

#### Fan Control

- `async set_chamber_fan_speed(speed: int) -> bool`  
  Sets chamber fan speed percentage (0-100).

- `async set_cooling_fan_speed(speed: int) -> bool`  
  Sets cooling fan speed percentage (0-100).

#### Print Settings

- `async set_speed_override(speed: int) -> bool`  
  Sets print speed override percentage.

- `async set_z_axis_override(offset: float) -> bool`  
  Sets Z-axis offset override.

#### Filament Sensor

- `async turn_runout_sensor_on() -> bool`  
  Enables filament runout sensor.

- `async turn_runout_sensor_off() -> bool`  
  Disables filament runout sensor.

---

### `flashforge.api.controls.JobControl`

Print job management and file operations.

#### Basic Job Control

- `async pause_print_job() -> bool`  
  Pauses current print job.

- `async resume_print_job() -> bool`  
  Resumes paused print job.

- `async cancel_print_job() -> bool`  
  Cancels current print job.

- `async clear_platform() -> bool`  
  Sends command to clear build platform.

#### File Upload & Printing

- `async upload_file(file_path: str, start_print: bool = True, level_before_print: bool = True) -> bool`  
  Uploads G-code/3MF file and optionally starts printing.

**Parameters:**
- `file_path` (str): Path to file to upload
- `start_print` (bool): Start printing after upload (default: True)
- `level_before_print` (bool): Perform bed leveling before print (default: True)

- `async print_local_file(file_name: str, leveling_before_print: bool = True) -> bool`  
  Starts printing a file already stored on the printer.

**Parameters:**
- `file_name` (str): Name of file on printer
- `leveling_before_print` (bool): Perform bed leveling (default: True)

#### AD5X-Specific Methods

- `async upload_file_ad5x(params: AD5XUploadParams) -> bool`  
  Uploads file to AD5X printer with material station support.

- `async start_ad5x_multi_color_job(params: AD5XLocalJobParams) -> bool`  
  Starts multi-color print job with material mappings.

- `async start_ad5x_single_color_job(params: AD5XSingleColorJobParams) -> bool`  
  Starts single-color print job on AD5X printer.

---

### `flashforge.api.controls.TempControl`

Temperature control for extruders and print bed.

#### Temperature Setting

- `async set_extruder_temp(temperature: int, wait_for: bool = False) -> bool`  
  Sets extruder target temperature in Celsius.

**Parameters:**
- `temperature` (int): Target temperature
- `wait_for` (bool): Wait for temperature to be reached (default: False)

- `async set_bed_temp(temperature: int, wait_for: bool = False) -> bool`  
  Sets bed target temperature in Celsius.

**Parameters:**
- `temperature` (int): Target temperature
- `wait_for` (bool): Wait for temperature to be reached (default: False)

#### Temperature Cancellation

- `async cancel_extruder_temp() -> bool`  
  Cancels extruder heating (sets target to 0).

- `async cancel_bed_temp() -> bool`  
  Cancels bed heating (sets target to 0).

#### Cooling

- `async wait_for_part_cool(target_temp: float = 50.0, timeout_seconds: int = 1800) -> bool`  
  Waits for components to cool to safe temperature.

**Parameters:**
- `target_temp` (float): Target temperature in Celsius (default: 50.0)
- `timeout_seconds` (int): Maximum wait time in seconds (default: 1800)

---

### `flashforge.api.controls.Files`

File operations and thumbnail retrieval.

#### File Listing

- `async get_file_list() -> List[str]`  
  Gets list of files stored locally on printer (via TCP).

- `async get_local_file_list() -> List[str]`  
  Alias for `get_file_list()`.

- `async get_recent_file_list() -> List[FFGcodeFileEntry]`  
  Gets list of 10 most recently printed files with metadata (via HTTP).

#### Thumbnails

- `async get_gcode_thumbnail(file_name: str) -> Optional[bytes]`  
  Retrieves thumbnail image for a G-code file as PNG bytes.

**Parameters:**
- `file_name` (str): Name of the G-code file

---

### `flashforge.api.controls.Info`

Information retrieval and status checking.

#### Machine Information

- `async get() -> Optional[FFMachineInfo]`  
  Gets comprehensive machine information.

- `async get_detail_response() -> Optional[DetailResponse]`  
  Gets raw detailed response from printer.

#### Status Checking

- `async is_printing() -> bool`  
  Checks if printer is currently printing.

- `async get_status() -> Optional[str]`  
  Gets raw status string (e.g., "ready", "printing").

- `async get_machine_state() -> Optional[MachineState]`  
  Gets machine state as enum value.

---

## TCP Client

### `flashforge.tcp.FlashForgeTcpClient`

Low-level TCP client for G-code commands and real-time status.

#### G-code Commands

- `async send_command_async(cmd: str) -> Optional[str]`  
  Sends raw G-code command and returns response.

#### File Operations

- `async get_file_list_async() -> List[str]`  
  Gets list of files on printer.

#### Status Parsers

- `async get_printer_info() -> Optional[PrinterInfo]`  
  Gets printer hardware information.

- `async get_temp_info() -> Optional[TempInfo]`  
  Gets temperature readings.

- `async get_location_info() -> Optional[LocationInfo]`  
  Gets current axis positions.

- `async get_endstop_status() -> Optional[EndstopStatus]`  
  Gets machine status, endstops, and movement mode.

- `async get_print_status() -> Optional[PrintStatus]`  
  Gets print progress information.

- `async get_thumbnail(file_name: str) -> Optional[ThumbnailInfo]`  
  Gets thumbnail with metadata.

#### Convenience Methods

- `async is_printer_ready() -> bool`  
  Checks if printer is ready.

- `async get_current_print_file() -> Optional[str]`  
  Gets name of currently loaded file.

- `async get_print_progress() -> Tuple[float, float, int]`  
  Returns (layer_percent, sd_percent, current_layer).

- `async check_machine_state() -> str`  
  Gets machine state string.

#### Temperature Control

- `async set_extruder_temp(temperature: int, wait_for: bool = False) -> bool`  
  Sets extruder temperature via TCP.

- `async set_bed_temp(temperature: int, wait_for: bool = False) -> bool`  
  Sets bed temperature via TCP.

- `async cancel_extruder_temp() -> bool`  
  Cancels extruder heating.

- `async cancel_bed_temp() -> bool`  
  Cancels bed heating.

- `async wait_for_part_cool(target_temp: float = 50.0, timeout_seconds: int = 1800) -> bool`  
  Waits for cooling.

#### LED Control (TCP)

The TCP client provides direct G-code-based LED control using the M146 command. This is useful for:
- Printers with aftermarket LED installations not detected by the HTTP API
- Cases where the `led_control` capability flag is incorrectly `False`
- Direct TCP-only connections without HTTP API access

- `async led_on() -> bool`  
  Turns on LED lights using M146 G-code command (`~M146 r255 g255 b255 F0`).

- `async led_off() -> bool`  
  Turns off LED lights using M146 G-code command (`~M146 r0 g0 b0 F0`).

**Note:** The M146 command uses RGB parameters but only supports binary on/off control (255,255,255 for on, 0,0,0 for off). See the [LED Control example](../examples/led_control.py) for usage patterns.

---

## Data Models

### `flashforge.models.FFMachineInfo`

Structured printer status and information.

**Key Properties:**
- `name: str` - Printer name
- `machine_state: MachineState` - Current state enum
- `status: str` - Raw status string
- `is_pro: bool` - Pro model flag
- `is_ad5x: bool` - AD5X model flag
- `firmware_version: str` - Firmware version
- `ip_address: str` - IP address
- `mac_address: str` - MAC address
- `print_file_name: str` - Current print file
- `print_progress: float` - Print progress (0.0-100.0)
- `current_print_layer: int` - Current layer number
- `total_print_layers: int` - Total layers
- `print_duration: int` - Print time in seconds
- `extruder: Temperature` - Extruder temperatures
- `print_bed: Temperature` - Bed temperatures
- `lights_on: bool` - LED status
- `door_open: bool` - Door status
- `error_code: str` - Error code if any

### `flashforge.models.Temperature`

Temperature readings for a component.

**Properties:**
- `current: float` - Current temperature in Celsius
- `set: float` - Target temperature in Celsius

### `flashforge.models.MachineState`

Enum for printer operational states.

**Values:**
- `READY` - Printer is ready
- `BUSY` - Printer is busy
- `PRINTING` - Actively printing
- `PAUSED` - Print is paused
- `COMPLETED` - Print completed
- `ERROR` - Error state
- `HEATING` - Heating components
- `CALIBRATING` - Performing calibration
- `CANCELLED` - Print cancelled
- `UNKNOWN` - Unknown state

### `flashforge.models.FFPrinterDetail`

Raw printer detail response from API. Contains all raw fields from the printer's HTTP API.

### `flashforge.tcp.parsers.PrinterInfo`

Printer hardware information from TCP.

**Properties:**
- `type_name: str` - Printer type
- `firmware_name: str` - Firmware name
- `x_size: int` - Build volume X (mm)
- `y_size: int` - Build volume Y (mm)
- `z_size: int` - Build volume Z (mm)

### `flashforge.tcp.parsers.TempInfo`

Temperature information from TCP.

**Methods:**
- `get_extruder_temp() -> Optional[Temperature]` - Get extruder temperatures
- `get_bed_temp() -> Optional[Temperature]` - Get bed temperatures

### `flashforge.tcp.parsers.LocationInfo`

Current axis positions.

**Properties:**
- `x_pos: float` - X position (mm)
- `y_pos: float` - Y position (mm)
- `z_pos: float` - Z position (mm)

### `flashforge.tcp.parsers.EndstopStatus`

Machine status and endstop information.

**Properties:**
- `machine_status: MachineStatus` - Machine status enum
- `move_mode: MoveMode` - Movement mode enum
- `led_enabled: bool` - LED status
- `current_file: Optional[str]` - Currently loaded file
- `endstop: Optional[Endstop]` - Endstop states

**Methods:**
- `is_printing() -> bool` - Check if printing
- `is_ready() -> bool` - Check if ready
- `is_paused() -> bool` - Check if paused
- `is_print_complete() -> bool` - Check if print complete

### `flashforge.tcp.parsers.PrintStatus`

Print progress information.

**Methods:**
- `get_layer_progress() -> str` - Layer progress string
- `get_print_percent() -> float` - Layer progress percentage
- `get_sd_progress() -> str` - SD card progress string
- `get_sd_percent() -> float` - SD card progress percentage
- `is_complete() -> bool` - Check if print complete

### `flashforge.tcp.parsers.ThumbnailInfo`

Thumbnail image data and metadata.

**Methods:**
- `has_image_data() -> bool` - Check if thumbnail exists
- `get_image_size() -> Tuple[int, int]` - Get (width, height)
- `get_image_bytes() -> Optional[bytes]` - Get raw PNG bytes
- `to_base64_data_url() -> Optional[str]` - Get base64 data URL
- `save_to_file_sync(path: str) -> bool` - Save to file

---

## Usage Examples

### Basic Connection

```python
from flashforge import FlashForgeClient

async with FlashForgeClient("192.168.1.100", "SERIAL", "CHECK_CODE") as client:
    if await client.initialize():
        status = await client.get_printer_status()
        print(f"Printer: {status.name}, State: {status.machine_state.value}")
```

### Discovery

```python
from flashforge import FlashForgePrinterDiscovery

discovery = FlashForgePrinterDiscovery()
printers = await discovery.discover_printers_async()

for printer in printers:
    print(f"{printer.name} at {printer.ip_address}")
```

### Temperature Control

```python
# Set temperatures
await client.temp_control.set_extruder_temp(200)
await client.temp_control.set_bed_temp(60)

# Wait for heating
await client.temp_control.set_extruder_temp(200, wait_for=True)

# Cool down
await client.temp_control.wait_for_part_cool(target_temp=50.0)
```

### File Operations

```python
# List files
files = await client.files.get_file_list()
print(f"Found {len(files)} files")

# Get thumbnail
thumbnail_bytes = await client.files.get_gcode_thumbnail("model.gcode")
if thumbnail_bytes:
    with open("thumbnail.png", "wb") as f:
        f.write(thumbnail_bytes)
```

### Job Control

```python
# Upload and print
await client.job_control.upload_file("model.gcode", start_print=True)

# Control print
await client.job_control.pause_print_job()
await client.job_control.resume_print_job()
await client.job_control.cancel_print_job()
```
