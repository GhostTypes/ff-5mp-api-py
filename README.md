<div align="center">

# FlashForge Python API

A comprehensive Python library for controlling FlashForge 3D printers.

[![PyPI](https://img.shields.io/pypi/v/flashforge-python-api?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/flashforge-python-api/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)

</div>

<div align="center">

## Features & Capabilities

| Feature | Description |
| :--- | :--- |
| **Printer Discovery** | Automatic UDP broadcast discovery of printers on the network |
| **Full Control** | Movement (G1), Homing (G28), Temperature (M104/M140), Fans, LED |
| **Real-time Monitoring** | Live status (M119), Temperatures (M105), Print Progress (M27) |
| **Job Management** | Start, Pause, Resume, Cancel, File Upload & Listing |
| **Advanced Parsing** | Thumbnail extraction (M662), Endstop monitoring, Machine state |
| **Dual Protocol** | Modern HTTP API + Legacy TCP G-code support |
| **Async Support** | Native async/await implementation for all operations |
| **Type Safety** | Full type hints and Pydantic models for robust development |

<br>

## Supported Hardware

| Model | Support Level | Connection Type |
| :--- | :--- | :--- |
| **FlashForge Adventurer 5M / 5M Pro** | Full Support | HTTP + TCP |
| **FlashForge Adventurer 5X** | Full Support | HTTP + TCP |
| **FlashForge Adventurer 3 / 4** | Partial Support | TCP (Legacy) |
| **Other Networked FlashForge Printers** | Experimental | TCP (Generic) |

<br>

## Compatible Slicers

| Slicer | Compatibility | Notes |
| :--- | :--- | :--- |
| **OrcaSlicer** | High | Recommended for Adventurer 5M series |
| **FlashPrint** | Full | Official FlashForge slicer |
| **Orca-FlashForge** | High | Optimized for FlashForge printers |
| **Cura / PrusaSlicer** | Basic | Requires correct G-code flavor |

<br>

## Installation

| Command |
| :--- |
| `pip install flashforge-python-api` |

</div>

<div align="center">
<h2>Usage Examples</h2>
</div>

<div align="center">
<h3>Printer Discovery</h3>
Discover printers on your local network automatically.
</div>

```python
from flashforge import FlashForgePrinterDiscovery
import asyncio

async def discover():
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()
    for printer in printers:
        print(f"Found: {printer.name} at {printer.ip_address}")

asyncio.run(discover())
```

<div align="center">
<h3>Basic Control</h3>
Connect to a printer and perform basic operations like setting temperature and homing.
</div>

```python
from flashforge import FlashForgeClient
import asyncio

async def control_printer():
    # Initialize client with printer details
    client = FlashForgeClient("192.168.1.100", "SERIAL_NUMBER", "CHECK_CODE")

    if await client.initialize():
        print(f"Connected to {client.printer_name}")

        # Set bed temperature to 60°C
        await client.temp_control.set_bed_temp(60)

        # Home all axes
        await client.control.home_xyz()

        await client.dispose()

asyncio.run(control_printer())
```

<div align="center">
<h3>Real-time Status Monitoring</h3>
Monitor printer status, temperatures, and print progress.
</div>

```python
from flashforge import FlashForgeClient
import asyncio

async def monitor_printer():
    async with FlashForgeClient("192.168.1.100", "SERIAL", "CODE") as client:
        # Get comprehensive status
        status = await client.get_printer_status()
        print(f"Machine State: {status.machine_state}")

        # Get temperatures via TCP
        temps = await client.tcp_client.get_temp_info()
        if temps:
            bed = temps.get_bed_temp()
            extruder = temps.get_extruder_temp()
            print(f"Bed: {bed.get_current()}°C / {bed.get_target()}°C")
            print(f"Extruder: {extruder.get_current()}°C / {extruder.get_target()}°C")

        # Check print progress
        layer_p, sd_p, current_layer = await client.tcp_client.get_print_progress()
        print(f"Progress: {layer_p}% (Layer {current_layer})")

asyncio.run(monitor_printer())
```

<div align="center">
<h3>File Operations & Thumbnails</h3>
List files on the printer and extract thumbnails.
</div>

```python
from flashforge import FlashForgeClient
import asyncio

async def file_ops():
    async with FlashForgeClient("192.168.1.100", "SERIAL", "CODE") as client:
        # List files
        files = await client.files.get_file_list()
        for filename in files:
            print(f"File: {filename}")

            # Get thumbnail
            thumb = await client.tcp_client.get_thumbnail(filename)
            if thumb and thumb.has_image_data():
                print(f"Thumbnail found: {len(thumb.get_image_bytes())} bytes")
                # thumb.save_to_file_sync(f"{filename}.png")

asyncio.run(file_ops())
```
