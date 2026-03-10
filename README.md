# FlashForge Python API

Python library for controlling FlashForge 3D printers with async support for the modern HTTP API and the legacy TCP protocol.

## Supported Printers

| Printer | Support |
| --- | --- |
| Adventurer 5M | Full |
| Adventurer 5M Pro | Full |
| AD5X | Full |
| Adventurer 3 / 4 | TCP support |

## Installation

```bash
pip install flashforge-python-api
```

## Quick Start

Modern LAN-mode HTTP printers require:

- printer IP address
- serial number
- check code

```python
import asyncio
from flashforge import FlashForgeClient, PrinterDiscovery


async def main():
    discovery = PrinterDiscovery()
    printers = await discovery.discover()

    if not printers:
        print("No printers found")
        return

    printer = printers[0]

    async with FlashForgeClient(
        printer.ip_address,
        printer.serial_number or "SERIAL_NUMBER",
        "CHECK_CODE",
    ) as client:
        if not await client.initialize():
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
- `FlashForgeTcpClient` and `client.tcp_client`: lower-level TCP access for direct commands and legacy workflows

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
