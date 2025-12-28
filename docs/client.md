# Getting Started

This guide will help you quickly get started with the FlashForge Python API.

## Installation

```bash
pip install flashforge-api
```

## Quick Start

### 1. Discover Printers

Find printers on your local network:

```python
import asyncio
from flashforge import FlashForgePrinterDiscovery

async def discover():
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()
    
    for printer in printers:
        print(f"{printer.name} at {printer.ip_address}")
    
    return printers

printers = asyncio.run(discover())
```

### 2. Connect to Printer

Connect using the discovered printer information:

```python
from flashforge import FlashForgeClient

async def connect():
    # Use discovered printer info
    async with FlashForgeClient(
        ip_address="192.168.1.100",
        serial_number="SERIAL_NUMBER",
        check_code=""  # Usually empty for local control
    ) as client:
        # Initialize connection
        if await client.initialize():
            print(f"Connected to {client.printer_name}")
            
            # Initialize control interface
            await client.init_control()
            
            # Get printer status
            status = await client.get_printer_status()
            print(f"Status: {status.machine_state.value}")
            print(f"Progress: {status.print_progress}%")

asyncio.run(connect())
```

### 3. Basic Operations

#### Get Printer Status

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    
    status = await client.get_printer_status()
    print(f"State: {status.machine_state.value}")
    print(f"Extruder: {status.extruder.current}°C / {status.extruder.set}°C")
    print(f"Bed: {status.print_bed.current}°C / {status.print_bed.set}°C")
```

#### Control Temperature

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    await client.init_control()
    
    # Set temperatures
    await client.temp_control.set_extruder_temp(200)
    await client.temp_control.set_bed_temp(60)
    
    # Wait for heating
    await client.temp_control.set_extruder_temp(200, wait_for=True)
```

#### Control Print Job

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    await client.init_control()
    
    # Pause/resume
    await client.job_control.pause_print_job()
    await client.job_control.resume_print_job()
    
    # Cancel
    await client.job_control.cancel_print_job()
```

#### List Files

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    
    # Get files on printer
    files = await client.files.get_file_list()
    for file in files:
        print(f"File: {file}")
    
    # Get recent files with metadata
    recent = await client.files.get_recent_file_list()
    for entry in recent:
        print(f"{entry.gcode_file_name} - {entry.printing_time}s")
```

#### Upload and Print

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    await client.init_control()
    
    # Upload and start printing
    await client.job_control.upload_file(
        "model.gcode",
        start_print=True,
        level_before_print=True
    )
```

## Complete Example

Here's a complete example showing discovery and basic operations:

```python
import asyncio
from flashforge import FlashForgeClient, FlashForgePrinterDiscovery

async def main():
    # Discover printers
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()
    
    if not printers:
        print("No printers found")
        return
    
    # Use first printer
    printer = printers[0]
    print(f"Connecting to {printer.name} at {printer.ip_address}")
    
    # Connect and use
    async with FlashForgeClient(
        printer.ip_address,
        printer.serial_number,
        ""
    ) as client:
        # Initialize
        if not await client.initialize():
            print("Failed to connect")
            return
        
        print(f"Connected to {client.printer_name}")
        print(f"Firmware: {client.firmware_version}")
        
        # Initialize control
        await client.init_control()
        
        # Get status
        status = await client.get_printer_status()
        print(f"\nStatus: {status.machine_state.value}")
        print(f"Extruder: {status.extruder.current}°C")
        print(f"Bed: {status.print_bed.current}°C")
        
        # List files
        files = await client.files.get_file_list()
        print(f"\nFiles on printer: {len(files)}")
        
        # Control LEDs
        await client.control.set_led_on()
        await asyncio.sleep(1)
        await client.control.set_led_off()
        
        # Note: If led_control capability is False, you can use TCP fallback:
        # await client.tcp_client.led_on()
        # await client.tcp_client.led_off()
        # See advanced.md for dual-mode LED control examples

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- **[API Reference](api_reference.md)** - Complete API documentation
- **[Advanced Topics](advanced.md)** - Async patterns, error handling, advanced features
- **[Data Models](models.md)** - Detailed model documentation
- **[Protocols](protocols.md)** - Low-level protocol details

## Common Patterns

### Context Manager (Recommended)

Always use the async context manager for automatic cleanup:

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    # ... use client ...
# Automatic cleanup
```

### Error Handling

Handle connection errors gracefully:

```python
try:
    async with FlashForgeClient(ip, serial, check_code) as client:
        if not await client.initialize():
            print("Failed to initialize")
            return
        
        # ... operations ...
        
except Exception as e:
    print(f"Error: {e}")
```

### Checking Printer State

Always check printer state before operations:

```python
status = await client.get_printer_status()

if status.machine_state == MachineState.PRINTING:
    print("Printer is busy")
elif status.machine_state == MachineState.READY:
    # Safe to start operations
    pass
```

## Troubleshooting

### Discovery Not Finding Printers

- Ensure printer and computer are on same network
- Check firewall settings
- Try manual connection with IP address

### Connection Failed

- Verify IP address is correct
- Ensure printer is powered on
- Check network connectivity
- Try `ping <printer_ip>`

### Commands Not Working

- Ensure `init_control()` was called after `initialize()`
- Check printer state (must be READY for most operations)
- Verify printer model supports the feature

## Support

For detailed API documentation, see [API Reference](api_reference.md).

For advanced usage patterns, see [Advanced Topics](advanced.md).
