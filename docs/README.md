# FlashForge Python API Documentation

This documentation covers the Python surface for `flashforge-python-api`.

## Before You Start

This repository and `@ghosttypes/ff-api` share the same protocol/domain baseline, but they do not promise strict 1:1 public API parity.

Read [parity.md](parity.md) first if you are comparing both libraries or maintaining downstream integrations across both languages.

## Documentation Structure

- [Getting Started](client.md)
- [Parity Notes](parity.md)
- [API Reference](api_reference.md)
- [Data Models](models.md)
- [Protocols](protocols.md)
- [Advanced Usage](advanced.md)

## Recommended Entry Points

- `FlashForgeClient` for modern printer access
- `PrinterDiscovery` for new discovery code
- `FlashForgePrinterDiscovery` only when you need compatibility with older Python callers

For modern HTTP printers, the check code is a per-printer credential and must come from user input or saved config.

## Quick Example

```python
import asyncio
import os
from flashforge import FlashForgeClient, FiveMClientConnectionOptions, PrinterDiscovery


async def main():
    check_code = os.getenv("FLASHFORGE_CHECK_CODE", "").strip()
    if not check_code:
        print("Set FLASHFORGE_CHECK_CODE before running this example")
        return

    discovery = PrinterDiscovery()
    printers = await discovery.discover()

    if not printers:
        print("No printers found")
        return

    printer = printers[0]
    if not printer.serial_number:
        print("Discovered printer did not report a serial number")
        return

    options = FiveMClientConnectionOptions(
        http_port=printer.event_port,
        tcp_port=printer.command_port,
    )

    async with FlashForgeClient(
        printer.ip_address,
        printer.serial_number,
        check_code,
        options=options,
    ) as client:
        status = await client.get_printer_status()
        if not status:
            return

        status = await client.get_printer_status()
        print(status.machine_state)


asyncio.run(main())
```
