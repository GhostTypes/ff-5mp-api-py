# FlashForge Python API

Python library for controlling FlashForge 3D printers with async support for the modern HTTP API and the legacy TCP protocol.

## Supported Printers

| Printer | Support |
| --- | --- |
| Adventurer 5M | Full |
| Adventurer 5M Pro | Full |
| AD5X | Full |
| Creator 5 | Full (HTTP-only) |
| Creator 5 Pro | Full (HTTP-only) |
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
- temperature and motion control, including per-nozzle and chamber temperature control (Creator 5)
- LED, camera, and filtration control where supported
- AD5X and Creator 5 / Creator 5 Pro material-station, slot configuration, and material mapping
- sliced 3MF parsing: read the tools, materials, colors, estimates, and thumbnail of a `.3mf` before upload

## Parse a Sliced 3MF

A sliced 3MF tells you which filaments (tools) a print uses. The Creator 5 series does not report this for stored files, so read the 3MF before you upload it. Then build one material mapping per filament.

```python
import asyncio
from flashforge import AD5XMaterialMapping, parse_3mf


async def build_mappings(path: str) -> list[AD5XMaterialMapping]:
    # parse_3mf is synchronous file I/O, so run it in a worker thread.
    info = await asyncio.to_thread(parse_3mf, path)
    print(f"{info.file_name}: {info.tool_count} tool(s), sliced for {info.printer_family}")

    mappings = []
    for filament in info.filaments:
        mappings.append(
            AD5XMaterialMapping(
                tool_id=filament.tool_id,      # 0-based: filament 1 is tool 0
                slot_id=filament.tool_id + 1,  # choose the station slot to print from
                material_name=filament.material_name,
                tool_material_color=filament.color or "#FFFFFF",
                slot_material_color=filament.color or "#FFFFFF",
            )
        )
    return mappings
```

In a real app, pick `slot_id` and `slot_material_color` from the slots the printer reports. Pass the mappings to `upload_file_creator5` / `start_creator5_job` (Creator 5 series) or `upload_file_ad5x` (AD5X).

`parse_3mf` accepts one sliced plate only. A project file with no sliced G-code raises `ThreeMFNotSlicedError`. A file with more than one sliced plate raises `ThreeMFMultiplePlatesError`. All 3MF errors subclass `ThreeMFError`.

## Documentation

- [docs/README.md](docs/README.md)
- [docs/client.md](docs/client.md)
- [docs/protocols.md](docs/protocols.md)
- [docs/api_reference.md](docs/api_reference.md)
