# FlashForge Python API Documentation

Complete documentation for controlling FlashForge 3D printers with Python.

## Documentation Structure

### Getting Started
- **[Getting Started Guide](client.md)** - Quick start guide for new users with basic examples

### Core Documentation
- **[API Reference](api_reference.md)** - Complete API documentation for all classes and methods
- **[Data Models](models.md)** - Detailed documentation of all data structures and models
- **[Protocols](protocols.md)** - Technical details about TCP, HTTP, and UDP protocols

### Advanced Topics
- **[Advanced Usage](advanced.md)** - Async patterns, error handling, and advanced features

## Quick Links

### Common Tasks

| Task | Documentation |
|------|--------------|
| Connect to printer | [Getting Started](client.md#quick-start) |
| Control temperature | [Getting Started](client.md#temperature-control) |
| Manage print jobs | [Getting Started](client.md#job-control) |
| List and manage files | [Getting Started](client.md#file-operations) |
| Monitor printer status | [API Reference](api_reference.md#flashforgeclient) |

### API Components

| Component | Documentation |
|-----------|--------------|
| FlashForgeClient | [API Reference](api_reference.md#flashforgeclient) |
| Discovery | [API Reference](api_reference.md#flashforgeprinterdiscovery) |
| Control modules | [API Reference](api_reference.md#control-modules) |
| TCP client | [API Reference](api_reference.md#tcp-client) |
| Data models | [Data Models](models.md) |

## Quick Example

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

    # Connect to first printer
    printer = printers[0]
    async with FlashForgeClient(
        printer.ip_address,
        printer.serial_number,
        printer.check_code
    ) as client:
        await client.initialize()

        # Get status
        status = await client.get_printer_status()
        print(f"Status: {status.machine_state.value}")
        print(f"Extruder: {status.extruder.current}°C")
        print(f"Bed: {status.print_bed.current}°C")

asyncio.run(main())
```

## Key Features

- **Dual Protocol Support** - Automatic HTTP and TCP protocol handling
- **Type Safety** - Full type hints and Pydantic models
- **Async/Await** - Non-blocking operations for efficient control
- **Comprehensive** - Complete coverage of printer capabilities
- **Well Documented** - Detailed documentation with examples

## Supported Printers

- Adventurer 5M / 5M Pro
- AD5X (with material station support)
- Adventurer 3 / 4 (basic support)
- Other FlashForge models (experimental)

## Documentation Navigation

1. **New to the API?** Start with [Getting Started](client.md)
2. **Looking for a specific method?** Check [API Reference](api_reference.md)
3. **Need model details?** See [Data Models](models.md)
4. **Want advanced patterns?** Read [Advanced Usage](advanced.md)
5. **Understanding protocols?** Review [Protocols](protocols.md)

## External Links

- [GitHub Repository](https://github.com/GhostTypes/ff-5mp-api-py)
- [PyPI Package](https://pypi.org/project/flashforge-python-api/)
- [Report Issues](https://github.com/GhostTypes/ff-5mp-api-py/issues)
