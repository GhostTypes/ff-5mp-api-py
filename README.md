# FlashForge Python API

Python library for controlling FlashForge 3D printers with async support for the modern HTTP API and the legacy TCP protocol.

## Supported Printers

| Printer | Support |
| --- | --- |
| Adventurer 5M | Full |
| Adventurer 5M Pro | Full |
| AD5X | Full |
| Adventurer 3 / 4 | Dedicated TCP clients |

## Installation

```bash
pip install flashforge-python-api
```

## Quick Start

Modern LAN-mode HTTP printers require:

- printer IP address
- serial number
- check code (per-printer credential, not returned by discovery)

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

        await client.init_control()

        status = await client.get_printer_status()
        print(f"Printer: {client.printer_name}")
        print(f"State: {status.machine_state if status else 'unknown'}")

        await client.control.home_axes()


asyncio.run(main())
```

## Main Entry Points

- `FlashForgeClient`: primary client for modern printers
- `PrinterDiscovery`: recommended discovery API
- `FlashForgeA4Client`: documented TCP client for Adventurer 4 Lite / Pro printers
- `FlashForgeA3Client`: documented TCP client for Adventurer 3 printers
- `FlashForgeTcpClient` and `client.tcp_client`: lower-level TCP access for direct commands and generic legacy workflows

## Capabilities

- printer discovery
- printer status and machine information
- job control
- file listing, uploads, and thumbnails
- temperature and motion control
- LED, camera, and filtration control where supported
- AD5X-specific job and material-station support

## Documentation

- [docs/README.md](docs/README.md)
- [docs/client.md](docs/client.md)
- [docs/protocols.md](docs/protocols.md)
- [docs/api_reference.md](docs/api_reference.md)
