# Data Models

The FlashForge API uses Pydantic models to ensure type safety and provide structured access to printer data. These models are defined in `flashforge.models`.

## FFMachineInfo

The `FFMachineInfo` class is the primary model for printer status. It aggregates data from various sources into a clean, easy-to-use structure.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `machine_state` | `MachineState` | Enum representing the current state (READY, PRINTING, ERROR, etc.). |
| `status` | `str` | Raw status string from the printer. |
| `print_bed` | `Temperature` | Current and target temperature of the heated bed. |
| `extruder` | `Temperature` | Current and target temperature of the nozzle. |
| `print_progress` | `float` | Completion percentage (0.0 to 100.0). |
| `print_eta` | `str` | Estimated time remaining ("MM:SS" or "HH:MM:SS"). |
| `current_print_layer` | `int` | The layer currently being printed. |
| `door_open` | `bool` | True if the enclosure door is open. |
| `lights_on` | `bool` | True if the LED lights are on. |

### Temperature

Represents a temperature reading.

```python
class Temperature(BaseModel):
    current: float  # Current temperature in Celsius
    set: float      # Target temperature in Celsius
```

### MachineState (Enum)

```python
class MachineState(Enum):
    READY = "ready"
    BUSY = "busy"
    CALIBRATING = "calibrating"
    ERROR = "error"
    HEATING = "heating"
    PRINTING = "printing"
    PAUSING = "pausing"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    UNKNOWN = "unknown"
```

## Material Station Models

For printers equipped with a material station (like the AD5X), additional models provide information about filament slots.

### MatlStationInfo

Detailed information about the material station.

| Field | Type | Description |
|-------|------|-------------|
| `current_load_slot` | `int` | ID of the slot currently loading. |
| `current_slot` | `int` | ID of the active/printing slot. |
| `slot_cnt` | `int` | Total number of slots. |
| `slot_infos` | `list[SlotInfo]` | List of info for each slot. |

### SlotInfo

Information about a single filament slot.

| Field | Type | Description |
|-------|------|-------------|
| `has_filament` | `bool` | Whether filament is present. |
| `material_name` | `str` | Type of material (e.g., "PLA"). |
| `material_color` | `str` | Hex color code (e.g., "#FF0000"). |

## G-code File Info

When listing files or checking job status, these models are used.

### FFGcodeFileEntry

Represents a print file on the printer.

| Field | Type | Description |
|-------|------|-------------|
| `gcode_file_name` | `str` | Name of the file. |
| `printing_time` | `int` | Estimated print time in seconds. |
| `total_filament_weight` | `float` | Estimated filament usage. |

## Raw API Models

You may also encounter `FFPrinterDetail`. This mimics the raw JSON structure returned by the printer's HTTP API. In most cases, you should prefer `FFMachineInfo`, which parses this raw data into a more Pythonic format.
