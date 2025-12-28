# Advanced Topics

## Async/Await Patterns

The FlashForge API is fully asynchronous, leveraging Python's `asyncio` library. All network operations are non-blocking, ensuring your application remains responsive while communicating with the printer.

### Best Practices

1.  **Always use `await`**: All methods interacting with the network are coroutines and must be awaited.
2.  **Context Managers**: Use `async with` for the client to ensure connections are properly closed and resources are cleaned up.
3.  **Concurrency**: You can run multiple commands in parallel using `asyncio.gather()`, but be careful with commands that modify printer state (like movement), as the printer processes G-code sequentially.

### Example: Concurrent Status Checks

```python
import asyncio
from flashforge import FlashForgeClient

async def check_multiple_printers(printer_configs):
    """Check status of multiple printers concurrently."""
    async def get_status(ip, serial, check_code):
        try:
            async with FlashForgeClient(ip, serial, check_code) as client:
                if await client.initialize():
                    status = await client.get_printer_status()
                    return {"ip": ip, "status": status, "error": None}
        except Exception as e:
            return {"ip": ip, "status": None, "error": str(e)}
    
    tasks = [get_status(cfg["ip"], cfg["serial"], cfg["check_code"]) 
             for cfg in printer_configs]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            print(f"Error: {result}")
        elif result["error"]:
            print(f"Printer {result['ip']}: Error - {result['error']}")
        else:
            print(f"Printer {result['ip']}: {result['status'].machine_state.value}")
```

### Example: Multiple Operations with Context Manager

```python
async def perform_maintenance_check():
    """Perform multiple operations on a single printer."""
    async with FlashForgeClient("192.168.1.100", "SERIAL", "CHECK_CODE") as client:
        # Initialize connection
        if not await client.initialize():
            print("Failed to connect")
            return
        
        # Initialize control interface
        await client.init_control()
        
        # Gather multiple status checks concurrently
        temps, status, files = await asyncio.gather(
            client.get_temperatures(),
            client.get_printer_status(),
            client.files.get_file_list()
        )
        
        print(f"Temperature: {temps}")
        print(f"Status: {status.machine_state.value}")
        print(f"Files: {len(files)} found")
```

## Error Handling

The API raises standard Python exceptions when network errors occur or when the printer returns invalid data. Proper error handling ensures your application can gracefully handle connection issues, timeouts, and printer errors.

### Common Exceptions

*   **`aiohttp.ClientError`**: Base class for HTTP networking errors (connection refused, DNS failures, etc.)
*   **`aiohttp.ClientConnectorError`**: Specific connection errors (printer offline, wrong IP)
*   **`asyncio.TimeoutError`**: Raised when an operation exceeds its timeout duration
*   **`OSError`** / **`ConnectionRefusedError`**: TCP connection failures (printer not responding on TCP port)

### Handling Connection Failures

The `FlashForgeClient` includes automatic reconnection logic for TCP sockets. However, if the printer is powered off or the network is unavailable, you should handle these cases in your application.

```python
import asyncio
import aiohttp
from flashforge import FlashForgeClient

async def connect_with_retry(ip, serial, check_code, max_retries=3):
    """Attempt to connect to printer with retry logic."""
    for attempt in range(max_retries):
        try:
            client = FlashForgeClient(ip, serial, check_code)
            
            if await client.initialize():
                print(f"✅ Connected on attempt {attempt + 1}")
                return client
            else:
                print(f"❌ Initialization failed on attempt {attempt + 1}")
                
        except aiohttp.ClientConnectorError as e:
            print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
        except asyncio.TimeoutError:
            print(f"Timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return None

# Usage
async def main():
    client = await connect_with_retry("192.168.1.100", "SERIAL", "CHECK_CODE")
    
    if client:
        async with client:
            # Use the client
            status = await client.get_printer_status()
            print(f"Printer status: {status.machine_state.value}")
    else:
        print("Failed to connect after all retries")
```

### Graceful Cleanup

Always use context managers or explicitly call `dispose()` to ensure proper cleanup:

```python
# Recommended: Using context manager
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    # ... operations ...
# Cleanup happens automatically

# Alternative: Manual cleanup
client = FlashForgeClient(ip, serial, check_code)
try:
    await client.initialize()
    # ... operations ...
finally:
    await client.dispose()  # Stops keep-alive and closes connections
```

## Connection Management

The FlashForge API uses a dual-layer architecture combining HTTP and TCP protocols:

- **HTTP Layer**: Used for file operations, printer status, and control commands
- **TCP Layer**: Used for real-time G-code commands, temperature monitoring, and low-level status queries

### Initialization Sequence

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    # Step 1: Initialize connection and verify printer
    if not await client.initialize():
        print("Failed to initialize")
        return
    
    # Step 2: Initialize control interface (required for some operations)
    if not await client.init_control():
        print("Failed to initialize control")
        return
    
    # Now ready for all operations
    await client.control.set_led_on()
```

**What happens during initialization:**

1. `initialize()`: Establishes TCP connection, retrieves printer info, caches printer details
2. `init_control()`: Sends product command via HTTP, initializes TCP control interface, starts keep-alive mechanism

### Keep-Alive Mechanism

The TCP client automatically maintains the connection by periodically sending status commands. This prevents the printer from closing the socket due to inactivity.

- Keep-alive interval: 5-10 seconds (adjusts based on error count)
- Automatically started during `init_control()`
- Automatically stopped when using context manager or calling `dispose()`

You don't need to manage keep-alive manually—it's handled automatically.

### Dual-Mode LED Control

The FlashForge API provides two methods for LED control: HTTP-based (via `client.control.set_led_on()`) and TCP-based (via `client.tcp_client.led_on()`). The TCP method is useful when:

- The printer has aftermarket LED installations not detected by the HTTP API
- The `led_control` capability flag incorrectly reports `False`

#### Using TCP LED Control as Fallback

```python
async def control_leds_with_fallback(client: FlashForgeClient):
    """Control LEDs with automatic fallback to TCP if HTTP unavailable."""
    if client.led_control:
        # Use HTTP API (preferred method)
        print("Using HTTP API for LED control")
        await client.control.set_led_on()
        await asyncio.sleep(2)
        await client.control.set_led_off()
    else:
        # Fallback to TCP G-code control
        print("HTTP LED control unavailable, using TCP fallback")
        tcp_client = client.tcp_client
        
        await tcp_client.led_on()  # Sends: ~M146 r255 g255 b255 F0
        await asyncio.sleep(2)
        await tcp_client.led_off()  # Sends: ~M146 r0 g0 b0 F0
```

#### Standalone TCP LED Control

For direct TCP-only connections without the HTTP API:

```python
from flashforge.tcp.ff_client import FlashForgeClient as TcpClient

async def standalone_tcp_led_control():
    """Control LEDs using only TCP connection."""
    client = TcpClient("192.168.1.100")
    
    try:
        if not await client.connect():
            print("Failed to connect")
            return
        
        if not await client.init_control():
            print("Failed to initialize control")
            return
        
        # Direct TCP LED control
        await client.led_on()
        await asyncio.sleep(2)
        await client.led_off()
        
    finally:
        await client.disconnect()
```

**M146 Command Details:**
- Uses M146 G-code with RGB parameters: `~M146 r255 g255 b255 F0` (on) or `~M146 r0 g0 b0 F0` (off)
- Only supports binary on/off control, not custom colors

See the [LED Control example](../examples/led_control.py) for complete working code.


## Manual Connection (Without Discovery)

If printer discovery doesn't work (e.g., across subnets or VLANs), you can connect manually using the printer's IP address.

**Requirements:**
- IP address of the printer
- Serial number (required for HTTP API operations)
- Check code (authentication token)

```python
from flashforge import FlashForgeClient

# Direct connection with known credentials
client = FlashForgeClient(
    ip_address="192.168.1.100",
    serial_number="YOUR_SERIAL_NUMBER",
    check_code="YOUR_CHECK_CODE"
)

async with client:
    if await client.initialize():
        print(f"Connected to {client.printer_name}")
```

**Finding your credentials:**

The serial number and check code are printer-specific. Use the discovery method first to automatically retrieve these values:

```python
from flashforge import FlashForgePrinterDiscovery

discovery = FlashForgePrinterDiscovery()
printers = await discovery.discover_printers_async()

for printer in printers:
    print(f"IP: {printer.ip_address}")
    print(f"Serial: {printer.serial_number}")
```

## Type Hints & Safety

This library uses comprehensive Python type hints and Pydantic models for data validation. All responses are strongly typed, providing excellent IDE autocompletion and static analysis support.

### Working with Typed Models

```python
from flashforge import FlashForgeClient
from flashforge.models import FFMachineInfo, MachineState, Temperature

async def monitor_printer_state(client: FlashForgeClient) -> None:
    """Demonstrates type-safe printer monitoring."""
    # get_printer_status returns Optional[FFMachineInfo]
    info: FFMachineInfo | None = await client.get_printer_status()
    
    if not info:
        print("Failed to get printer status")
        return
    
    # IDE knows all available properties and their types
    state: MachineState = info.machine_state
    extruder: Temperature = info.extruder
    bed: Temperature = info.print_bed
    
    # Type-safe enum comparison
    if state == MachineState.PRINTING:
        print(f"Printing: {info.print_file_name}")
        print(f"Progress: {info.print_progress:.1f}%")
        print(f"Layer: {info.current_print_layer}/{info.total_print_layers}")
    elif state == MachineState.READY:
        print("Printer is ready")
    elif state == MachineState.ERROR:
        print(f"Error: {info.error_code}")
    
    # Temperature objects have typed properties
    print(f"Extruder: {extruder.current:.1f}°C / {extruder.set:.1f}°C")
    print(f"Bed: {bed.current:.1f}°C / {bed.set:.1f}°C")
```

### Type Safety with mypy

The library is fully compatible with `mypy` for static type checking:

```python
from flashforge import FlashForgeClient

async def get_printer_name(client: FlashForgeClient) -> str:
    """Returns printer name or 'Unknown' if unavailable."""
    status = await client.get_printer_status()
    
    # mypy knows status is Optional[FFMachineInfo]
    if status:
        return status.name  # mypy knows .name is str
    
    return "Unknown"

# mypy will catch type errors:
# name: int = await get_printer_name(client)  # Error: incompatible types
```

## G-code Thumbnails

FlashForge printers store thumbnail images for G-code files. You can retrieve these using either the HTTP API or the TCP client, depending on your needs.

### HTTP API Method (Recommended)

The HTTP API provides base64-encoded thumbnail data:

```python
async def download_thumbnail_http(client: FlashForgeClient, filename: str):
    """Download thumbnail using HTTP API."""
    thumbnail_bytes = await client.files.get_gcode_thumbnail(filename)
    
    if thumbnail_bytes:
        # Save to file
        with open(f"thumbnail_{filename}.png", "wb") as f:
            f.write(thumbnail_bytes)
        print(f"Saved thumbnail ({len(thumbnail_bytes)} bytes)")
    else:
        print("No thumbnail available")
```

### TCP Client Method (Advanced)

The TCP client provides a `ThumbnailInfo` parser with additional metadata and helper methods:

```python
async def download_thumbnail_tcp(client: FlashForgeClient, filename: str):
    """Download thumbnail using TCP client with metadata."""
    thumbnail_info = await client.tcp_client.get_thumbnail(filename)
    
    if thumbnail_info and thumbnail_info.has_image_data():
        # Get image dimensions
        width, height = thumbnail_info.get_image_size()
        print(f"Thumbnail: {width}x{height}px")
        
        # Save using built-in method
        if thumbnail_info.save_to_file_sync(f"thumbnail_{filename}.png"):
            print("Saved thumbnail")
        
        # Or get as base64 data URL for web display
        data_url = thumbnail_info.to_base64_data_url()
        if data_url:
            print(f"Data URL: {data_url[:100]}...")
        
        # Or get raw bytes
        image_bytes = thumbnail_info.get_image_bytes()
        print(f"Size: {len(image_bytes)} bytes")
    else:
        print("No thumbnail available")
```

**Note:** Thumbnails are typically PNG images. Not all G-code files have thumbnails—this depends on the slicer settings used when generating the file.

## Advanced TCP Parsers

The TCP client includes specialized parsers for detailed printer information beyond basic status queries.

### EndstopStatus Parser

Monitor machine state, movement mode, endstop status, and currently loaded file:

```python
async def check_machine_state(client: FlashForgeClient):
    """Get detailed machine state using EndstopStatus parser."""
    endstop_status = await client.tcp_client.get_endstop_status()
    
    if endstop_status:
        print(f"Machine Status: {endstop_status.machine_status.value}")
        print(f"Move Mode: {endstop_status.move_mode.value}")
        print(f"LED Enabled: {endstop_status.led_enabled}")
        print(f"Current File: {endstop_status.current_file or 'None'}")
        
        # Check endstop states (0 = not triggered, 1 = triggered)
        if endstop_status.endstop:
            print(f"Endstops - X:{endstop_status.endstop.x_max} "
                  f"Y:{endstop_status.endstop.y_max} "
                  f"Z:{endstop_status.endstop.z_min}")
        
        # Convenience methods
        if endstop_status.is_printing():
            print("Printer is actively printing")
        elif endstop_status.is_paused():
            print("Print is paused")
        elif endstop_status.is_ready():
            print("Printer is ready")
        elif endstop_status.is_print_complete():
            print("Print completed")
```

### PrintStatus Parser

Track print progress with layer and SD card information:

```python
async def monitor_print_progress(client: FlashForgeClient):
    """Monitor print progress using PrintStatus parser."""
    print_status = await client.tcp_client.get_print_status()
    
    if print_status:
        # Layer progress
        layer_progress = print_status.get_layer_progress()
        layer_percent = print_status.get_print_percent()
        print(f"Layer Progress: {layer_progress} ({layer_percent:.1f}%)")
        
        # SD card progress
        sd_progress = print_status.get_sd_progress()
        sd_percent = print_status.get_sd_percent()
        print(f"SD Progress: {sd_progress} ({sd_percent:.1f}%)")
        
        # Check completion
        if print_status.is_complete():
            print("Print is complete")
    else:
        print("No active print job")
```

### Convenience Methods

The TCP client provides high-level convenience methods that use these parsers internally:

```python
async def quick_status_check(client: FlashForgeClient):
    """Quick status check using convenience methods."""
    # Check if printer is ready
    is_ready = await client.tcp_client.is_printer_ready()
    print(f"Printer Ready: {is_ready}")
    
    # Get current print file
    current_file = await client.tcp_client.get_current_print_file()
    print(f"Current File: {current_file or 'None'}")
    
    # Get print progress (returns tuple)
    layer_percent, sd_percent, current_layer = await client.tcp_client.get_print_progress()
    print(f"Progress: Layer {layer_percent}%, SD {sd_percent}%, Layer #{current_layer}")
    
    # Check machine state
    machine_state = await client.tcp_client.check_machine_state()
    print(f"State: {machine_state}")
```

These parsers provide detailed, structured access to printer state information, enabling sophisticated monitoring and automation workflows.
