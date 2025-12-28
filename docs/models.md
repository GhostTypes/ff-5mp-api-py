# Data Models

The FlashForge API uses Pydantic models for type safety and structured data access. This document provides detailed information about all data models.

## Core Models

### FFMachineInfo

The primary model for printer status, aggregating data from various sources into a structured format.

**Import**: `from flashforge.models import FFMachineInfo`

#### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | User-defined printer name |
| `machine_state` | `MachineState` | Current operational state (enum) |
| `status` | `str` | Raw status string from printer |
| `is_pro` | `bool` | True if Pro model |
| `is_ad5x` | `bool` | True if AD5X series model |
| `firmware_version` | `str` | Firmware version string |
| `ip_address` | `str` | Printer IP address |
| `mac_address` | `str` | MAC address |

#### Temperature Properties

| Property | Type | Description |
|----------|------|-------------|
| `extruder` | `Temperature` | Extruder current and target temps |
| `print_bed` | `Temperature` | Bed current and target temps |

#### Print Job Properties

| Property | Type | Description |
|----------|------|-------------|
| `print_file_name` | `str` | Current print file name |
| `print_progress` | `float` | Progress percentage (0.0-100.0) |
| `print_progress_int` | `int` | Progress as integer (0-100) |
| `current_print_layer` | `int` | Current layer number |
| `total_print_layers` | `int` | Total layers in print |
| `print_duration` | `int` | Print time in seconds |
| `print_eta` | `str` | Estimated time remaining (formatted) |
| `formatted_run_time` | `str` | Formatted runtime string |

#### Hardware Status Properties

| Property | Type | Description |
|----------|------|-------------|
| `lights_on` | `bool` | LED lights status |
| `door_open` | `bool` | Enclosure door status |
| `error_code` | `str` | Error code if any |
| `chamber_fan_speed` | `int` | Chamber fan speed (0-100) |
| `cooling_fan_speed` | `int` | Cooling fan speed (0-100) |
| `external_fan_on` | `bool` | External filtration status |
| `internal_fan_on` | `bool` | Internal filtration status |

#### Cumulative Statistics

| Property | Type | Description |
|----------|------|-------------|
| `cumulative_filament` | `float` | Total filament used (meters) |
| `cumulative_print_time` | `int` | Total print time (seconds) |
| `free_disk_space` | `str` | Available storage space |

#### Cloud Integration

| Property | Type | Description |
|----------|------|-------------|
| `flash_cloud_register_code` | `str` | FlashCloud registration code |
| `polar_cloud_register_code` | `str` | PolarCloud registration code |

#### Material Station (AD5X)

| Property | Type | Description |
|----------|------|-------------|
| `has_matl_station` | `Optional[bool]` | Material station present |
| `matl_station_info` | `Optional[MatlStationInfo]` | Material station details |
| `indep_matl_info` | `Optional[IndepMatlInfo]` | Independent material info |

### Temperature

Represents temperature readings for a component.

**Import**: `from flashforge.models import Temperature`

```python
class Temperature(BaseModel):
    current: float  # Current temperature in Celsius
    set: float      # Target temperature in Celsius
```

**Usage**:
```python
status = await client.get_printer_status()
print(f"Extruder: {status.extruder.current}°C / {status.extruder.set}°C")
print(f"Bed: {status.print_bed.current}°C / {status.print_bed.set}°C")
```

### MachineState

Enum representing printer operational states.

**Import**: `from flashforge.models import MachineState`

```python
class MachineState(Enum):
    READY = "ready"           # Printer is ready for commands
    BUSY = "busy"             # Printer is busy
    CALIBRATING = "calibrating"  # Performing calibration
    ERROR = "error"           # Error state
    HEATING = "heating"       # Heating components
    PRINTING = "printing"     # Actively printing
    PAUSING = "pausing"       # Pausing print
    PAUSED = "paused"         # Print is paused
    CANCELLED = "cancelled"   # Print was cancelled
    COMPLETED = "completed"   # Print completed
    UNKNOWN = "unknown"       # Unknown state
```

**Usage**:
```python
status = await client.get_printer_status()

if status.machine_state == MachineState.PRINTING:
    print(f"Printing: {status.print_progress}% complete")
elif status.machine_state == MachineState.READY:
    print("Ready for new job")
elif status.machine_state == MachineState.ERROR:
    print(f"Error: {status.error_code}")
```

## Material Station Models (AD5X)

### MatlStationInfo

Detailed information about the material station on AD5X printers.

**Import**: `from flashforge.models import MatlStationInfo`

| Property | Type | Description |
|----------|------|-------------|
| `current_load_slot` | `int` | Slot ID currently loading (0 if none) |
| `current_slot` | `int` | Active/printing slot ID (0 if none) |
| `slot_cnt` | `int` | Total number of slots |
| `slot_infos` | `list[SlotInfo]` | Information for each slot |
| `state_action` | `int` | Current action state |
| `state_step` | `int` | Current step within action |

### SlotInfo

Information about a single filament slot.

**Import**: `from flashforge.models import SlotInfo`

| Property | Type | Description |
|----------|------|-------------|
| `slot_id` | `int` | Slot identifier |
| `has_filament` | `bool` | Filament present in slot |
| `material_name` | `str` | Material type (e.g., "PLA", "PETG") |
| `material_color` | `str` | Hex color code (e.g., "#FF0000") |

**Usage**:
```python
status = await client.get_printer_status()

if status.has_matl_station and status.matl_station_info:
    station = status.matl_station_info
    print(f"Material Station: {station.slot_cnt} slots")
    print(f"Active slot: {station.current_slot}")
    
    for slot in station.slot_infos:
        if slot.has_filament:
            print(f"Slot {slot.slot_id}: {slot.material_name} ({slot.material_color})")
```

### IndepMatlInfo

Independent material loading information (single extruder with material station).

**Import**: `from flashforge.models import IndepMatlInfo`

| Property | Type | Description |
|----------|------|-------------|
| `material_name` | `str` | Material name ("?" if unknown) |
| `material_color` | `str` | Material color hex code |
| `state_action` | `int` | Current action state |
| `state_step` | `int` | Current step within action |

## G-code File Models

### FFGcodeFileEntry

Represents a G-code file entry with metadata.

**Import**: `from flashforge.models import FFGcodeFileEntry`

| Property | Type | Description |
|----------|------|-------------|
| `gcode_file_name` | `str` | File name (e.g., "model.gcode") |
| `printing_time` | `int` | Estimated print time (seconds) |
| `gcode_tool_cnt` | `Optional[int]` | Number of tools/materials used |
| `gcode_tool_datas` | `Optional[list[FFGcodeToolData]]` | Tool/material details |
| `total_filament_weight` | `Optional[float]` | Total filament weight estimate |
| `use_matl_station` | `Optional[bool]` | Requires material station |

**Usage**:
```python
recent_files = await client.files.get_recent_file_list()

for entry in recent_files:
    hours = entry.printing_time // 3600
    minutes = (entry.printing_time % 3600) // 60
    print(f"{entry.gcode_file_name}: {hours}h {minutes}m")
    
    if entry.total_filament_weight:
        print(f"  Filament: {entry.total_filament_weight}g")
```

### FFGcodeToolData

Material/tool data for multi-material prints.

**Import**: `from flashforge.models import FFGcodeToolData`

| Property | Type | Description |
|----------|------|-------------|
| `tool_id` | `int` | Tool/extruder number |
| `slot_id` | `int` | Material station slot (0 if direct) |
| `material_name` | `str` | Material type (e.g., "PLA") |
| `material_color` | `str` | Hex color code |
| `filament_weight` | `float` | Filament weight for this tool |

## TCP Parser Models

### PrinterInfo

Hardware information from TCP connection.

**Import**: `from flashforge.tcp.parsers import PrinterInfo`

| Property | Type | Description |
|----------|------|-------------|
| `type_name` | `str` | Printer model name |
| `firmware_name` | `str` | Firmware name |
| `firmware_version` | `str` | Firmware version |
| `x_size` | `int` | Build volume X (mm) |
| `y_size` | `int` | Build volume Y (mm) |
| `z_size` | `int` | Build volume Z (mm) |
| `tool_count` | `int` | Number of extruders |

### TempInfo

Temperature information from TCP.

**Import**: `from flashforge.tcp.parsers import TempInfo`

**Methods**:
- `get_extruder_temp() -> Optional[Temperature]` - Get extruder temperatures
- `get_bed_temp() -> Optional[Temperature]` - Get bed temperatures

### LocationInfo

Current axis positions.

**Import**: `from flashforge.tcp.parsers import LocationInfo`

| Property | Type | Description |
|----------|------|-------------|
| `x_pos` | `float` | X position (mm) |
| `y_pos` | `float` | Y position (mm) |
| `z_pos` | `float` | Z position (mm) |

### EndstopStatus

Machine status and endstop information.

**Import**: `from flashforge.tcp.parsers import EndstopStatus`

| Property | Type | Description |
|----------|------|-------------|
| `machine_status` | `MachineStatus` | Machine status enum |
| `move_mode` | `MoveMode` | Movement mode enum |
| `led_enabled` | `bool` | LED status |
| `current_file` | `Optional[str]` | Currently loaded file |
| `endstop` | `Optional[Endstop]` | Endstop states |

**Methods**:
- `is_printing() -> bool` - Check if printing
- `is_ready() -> bool` - Check if ready
- `is_paused() -> bool` - Check if paused
- `is_print_complete() -> bool` - Check if complete

### PrintStatus

Print progress information.

**Import**: `from flashforge.tcp.parsers import PrintStatus`

**Methods**:
- `get_layer_progress() -> str` - Layer progress string
- `get_print_percent() -> float` - Layer progress percentage
- `get_sd_progress() -> str` - SD progress string
- `get_sd_percent() -> float` - SD progress percentage
- `is_complete() -> bool` - Check if complete

### ThumbnailInfo

Thumbnail image data and metadata.

**Import**: `from flashforge.tcp.parsers import ThumbnailInfo`

**Methods**:
- `has_image_data() -> bool` - Check if thumbnail exists
- `get_image_size() -> Tuple[int, int]` - Get (width, height)
- `get_image_bytes() -> Optional[bytes]` - Get raw PNG bytes
- `to_base64_data_url() -> Optional[str]` - Get base64 data URL
- `save_to_file_sync(path: str) -> bool` - Save to file

## Raw API Models

### FFPrinterDetail

Raw JSON structure from printer's HTTP API. Contains all raw fields in printer's native format.

**Import**: `from flashforge.models import FFPrinterDetail`

**Note**: In most cases, use `FFMachineInfo` instead, which parses this raw data into a more Pythonic format.

## Model Relationships

```
FlashForgeClient
    └── get_printer_status() -> FFMachineInfo
            ├── machine_state: MachineState (enum)
            ├── extruder: Temperature
            ├── print_bed: Temperature
            └── matl_station_info: MatlStationInfo (AD5X only)
                    └── slot_infos: List[SlotInfo]

    └── files.get_recent_file_list() -> List[FFGcodeFileEntry]
            └── gcode_tool_datas: List[FFGcodeToolData]

    └── tcp_client.get_printer_info() -> PrinterInfo
    └── tcp_client.get_temp_info() -> TempInfo
    └── tcp_client.get_endstop_status() -> EndstopStatus
    └── tcp_client.get_print_status() -> PrintStatus
    └── tcp_client.get_thumbnail() -> ThumbnailInfo
```

## Type Safety

All models use Pydantic for validation and type safety:

```python
from flashforge.models import FFMachineInfo, MachineState

# Type hints work correctly
status: FFMachineInfo = await client.get_printer_status()

# IDE autocomplete available
if status.machine_state == MachineState.PRINTING:
    progress: float = status.print_progress
    layer: int = status.current_print_layer
```

## See Also

- **[API Reference](api_reference.md)** - Complete API documentation
- **[Getting Started](client.md)** - Quick start guide
- **[Protocols](protocols.md)** - Low-level protocol details
