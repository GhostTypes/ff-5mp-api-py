# Getting Started

This guide covers the recommended modern Python API surface.

## Installation

```bash
pip install flashforge-python-api
```

## Discovery

For new code, prefer `PrinterDiscovery`.

```python
import asyncio
from flashforge import PrinterDiscovery


async def discover():
    discovery = PrinterDiscovery()
    printers = await discovery.discover()

    for printer in printers:
        print(f"{printer.name} at {printer.ip_address}")

    return printers


printers = asyncio.run(discover())
```

If you need the older Python compatibility surface, `FlashForgePrinterDiscovery` is still exported, but it only returns the reduced legacy wrapper objects.

## Connect to a Printer

Modern LAN-mode HTTP printers require the printer IP address, serial number, and check code.

```python
import asyncio
from flashforge import FlashForgeClient


async def connect():
    async with FlashForgeClient(
        ip_address="192.168.1.100",
        serial_number="SERIAL_NUMBER",
        check_code="CHECK_CODE",
    ) as client:
        if not await client.initialize():
            return

        await client.init_control()

        print(f"Connected to {client.printer_name}")
        print(f"Firmware: {client.firmware_version}")


asyncio.run(connect())
```

## Basic Operations

### Get Printer Status

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    status = await client.get_printer_status()
    print(status.machine_state)
```

### Control Temperature

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    await client.init_control()

    await client.temp_control.set_extruder_temp(200)
    await client.temp_control.set_bed_temp(60)
```

### Control Motion and Jobs

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()
    await client.init_control()

    await client.control.home_axes()
    await client.job_control.pause_print_job()
    await client.job_control.resume_print_job()
    await client.job_control.cancel_print_job()
```

Python also exposes some convenience wrappers on the top-level client, such as `pause_print()`, `resume_print()`, and `home_all_axes()`. These helpers are Python-specific and are not part of a strict cross-language parity contract.

### Detect OEM Camera Stream

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()

    if client.camera_stream_url:
        print(f"OEM camera stream: {client.camera_stream_url}")
```

### List Files

```python
async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()

    files = await client.files.get_file_list()
    recent = await client.files.get_recent_file_list()
```

## Compatibility Notes

- `FlashForgePrinterDiscovery` remains available for older Python callers.
- `PrinterDiscovery` is the preferred discovery API for new code.
- `init_control()` is still the correct method name in Python.
- Python convenience helpers and compatibility shims should not be assumed to exist in TypeScript.

## Next Steps

- [API Reference](api_reference.md)
- [Advanced Topics](advanced.md)
- [Parity Notes](parity.md)
