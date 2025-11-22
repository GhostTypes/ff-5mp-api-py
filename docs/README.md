# FlashForge API Documentation

Welcome to the documentation for the FlashForge Python API. This library provides a comprehensive interface for controlling and monitoring FlashForge 3D printers, including the Adventurer 5M and 5M Pro series.

## Overview

The FlashForge API allows you to interact with your printer using both TCP and HTTP protocols. It provides a unified client that handles connection management, command execution, and status monitoring.

## Key Features

- **Unified Client**: A single entry point (`FlashForgeClient`) for all printer operations.
- **Automatic Discovery**: Find printers on your local network automatically.
- **Full Control**: Manage print jobs, movement, temperature, fans, LEDs, and more.
- **Real-time Monitoring**: Get detailed status updates, including temperatures, progress, and camera feed URL.
- **File Management**: List, upload, and delete files on the printer.
- **Type Safety**: Fully typed with Pydantic models for robust data handling.
- **Async Support**: Built on `asyncio` for efficient non-blocking operations.

## Navigation

- [Getting Started](#getting-started)
- [Client API](client.md): Documentation for the main `FlashForgeClient` and `FlashForgePrinterDiscovery`.
- [Data Models](models.md): Detailed reference for all data objects (MachineInfo, Temperature, etc.).
- [Protocols](protocols.md): Understanding the underlying TCP and HTTP protocols.
- [Advanced Topics](advanced.md): Async patterns, error handling, and more.
- [API Reference](api_reference.md): Complete list of classes and methods.

## Getting Started

### Installation

```bash
pip install flashforge-api
```

### Basic Usage

Here's a simple example of how to discover a printer and connect to it:

```python
import asyncio
from flashforge import FlashForgePrinterDiscovery, FlashForgeClient

async def main():
    # 1. Discover printers
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()

    if not printers:
        print("No printers found.")
        return

    printer_info = printers[0]
    print(f"Found printer: {printer_info.name} at {printer_info.ip_address}")

    # 2. Connect to the printer
    # Note: 'check_code' is currently unused by some printers but required by the constructor
    client = FlashForgeClient(printer_info.ip_address, printer_info.serial_number, check_code="")

    await client.initialize()

    # 3. Get printer status
    status = await client.get_printer_status()
    print(f"Status: {status.machine_state}")
    print(f"Bed Temp: {status.print_bed.current}°C")
    print(f"Nozzle Temp: {status.extruder.current}°C")

    # 4. Clean up
    await client.dispose()

if __name__ == "__main__":
    asyncio.run(main())
```

### Context Manager Support

The client supports Python's async context manager protocol for automatic resource management:

```python
async with FlashForgeClient(ip, serial, check_code="") as client:
    status = await client.get_printer_status()
    print(f"Ready: {status.machine_state == 'ready'}")
```

## Support

If you encounter any issues or have questions, please check the [Issues](https://github.com/yourusername/flashforge-api/issues) page on GitHub.
