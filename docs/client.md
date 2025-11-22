# Client API

This section documents the primary classes you'll use to interact with FlashForge printers: `FlashForgeClient` and `FlashForgePrinterDiscovery`.

## FlashForgeClient

The `FlashForgeClient` is the main entry point for the API. It orchestrates communication with the printer using both HTTP and TCP protocols.

### Constructor

```python
FlashForgeClient(ip_address: str, serial_number: str, check_code: str)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `ip_address` | `str` | The IP address of the printer (e.g., "192.168.1.50"). |
| `serial_number` | `str` | The printer's serial number. |
| `check_code` | `str` | A verification code (often empty for local control). |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_ad5x` | `bool` | `True` if the printer is an Adventurer 5M series model. |
| `is_pro` | `bool` | `True` if the printer is a "Pro" model (e.g., Adventurer 5M Pro). |
| `printer_name` | `str` | The user-defined name of the printer. |
| `firmware_version` | `str` | The current firmware version. |
| `mac_address` | `str` | The printer's MAC address. |

### Core Methods

#### `initialize()`
Initializes the client and verifies the connection.
```python
success = await client.initialize()
```

#### `get_printer_status()`
Retrieves the full status of the printer.
```python
status: FFMachineInfo = await client.get_printer_status()
```

#### `get_temperatures()`
Gets the current temperature readings directly from the TCP connection.
```python
temps = await client.get_temperatures()
```

#### `dispose()`
Closes connections and cleans up resources.
```python
await client.dispose()
```

### Control Modules

The client exposes several control modules for specific functionality:

#### `client.control`
General printer controls (movement, fans, LEDs).
- `home_axes()`: Home all axes.
- `set_led_on()` / `set_led_off()`: Control built-in lights.
- `turn_camera_on()` / `turn_camera_off()`: Control the camera (Pro models).
- `set_external_filtration_on()`: Control air filtration.

#### `client.job_control`
Manage print jobs.
- `pause_print_job()`: Pause the current print.
- `resume_print_job()`: Resume a paused print.
- `cancel_print_job()`: Stop the current print immediately.

#### `client.files`
File management on the printer.
- `get_file_list()`: Get a list of files on the printer using TCP.
- `get_recent_file_list()`: Get a list of recent files using HTTP.
- `get_gcode_thumbnail(file_name)`: Get the thumbnail of a G-code file.

#### `client.temp_control`
Temperature management.
- `set_bed_temp(temp)`: Set target bed temperature.
- `set_extruder_temp(temp)`: Set target nozzle temperature.
- `cooldown()`: Turn off all heaters.

---

## FlashForgePrinterDiscovery

The `FlashForgePrinterDiscovery` class allows you to find printers on your local network using UDP broadcasting.

### Usage

```python
from flashforge import FlashForgePrinterDiscovery

discovery = FlashForgePrinterDiscovery()
printers = await discovery.discover_printers_async()
```

### Methods

#### `discover_printers_async(timeout_ms=10000, idle_timeout_ms=1500, max_retries=3)`

Discovers printers on the network.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `timeout_ms` | `10000` | Total time to wait for responses (milliseconds). |
| `idle_timeout_ms` | `1500` | Time to wait after the last received response (milliseconds). |
| `max_retries` | `3` | Number of times to retry discovery if no printers are found. |

**Returns**: A list of `FlashForgePrinter` objects.

### FlashForgePrinter Object

Represents a discovered printer.

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The printer's name. |
| `serial_number` | `str` | The serial number. |
| `ip_address` | `str` | The IP address. |
