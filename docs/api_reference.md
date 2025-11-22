# API Reference

This document provides a reference for the module organization and class hierarchy.

## `flashforge.client`

### `FlashForgeClient`
The main client class.

*   `__init__(ip_address, serial_number, check_code)`
*   `initialize()`
*   `dispose()`
*   `get_printer_status()`
*   `control` (Access to `Control` module)
*   `job_control` (Access to `JobControl` module)
*   `files` (Access to `Files` module)
*   `info` (Access to `Info` module)
*   `temp_control` (Access to `TempControl` module)

## `flashforge.discovery`

### `FlashForgePrinterDiscovery`
Handles UDP discovery.

*   `discover_printers_async()`

### `FlashForgePrinter`
Data class for discovery results.

*   `name`
*   `serial_number`
*   `ip_address`

## `flashforge.api.controls`

### `Control`
General machine control.
*   `home_axes()`
*   `set_led_on()`, `set_led_off()`
*   `turn_camera_on()`, `turn_camera_off()`
*   `set_chamber_fan_speed(speed)`
*   `set_cooling_fan_speed(speed)`
*   `set_external_filtration_on()`, `set_internal_filtration_on()`, `set_filtration_off()`

### `JobControl`
Print job management.
*   `pause_print_job()`
*   `resume_print_job()`
*   `cancel_print_job()`

### `TempControl`
Temperature management.
*   `set_bed_temp(temp)`
*   `set_extruder_temp(temp)`
*   `cooldown()`

### `Files`
File operations.
*   `get_file_list()`
*   `get_recent_file_list()`
*   `get_gcode_thumbnail(filename)`

## `flashforge.models`

### `FFMachineInfo`
High-level printer status.

### `Temperature`
Temperature readings.

### `MachineState`
Enum for printer state.

### `FFPrinterDetail`
Raw printer detail response.
