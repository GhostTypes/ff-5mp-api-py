<div align="center">

# FlashForge Python API

**A comprehensive Python library for controlling FlashForge 3D printers**

![PyPI](https://img.shields.io/pypi/v/flashforge-python-api?style=flat&color=3776ab) ![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=flat) ![License](https://img.shields.io/badge/License-MIT-brightgreen?style=flat) ![Status](https://img.shields.io/badge/Status-Stable-brightgreen?style=flat)

![aiohttp](https://img.shields.io/badge/aiohttp-%E2%89%A53.8.0-blue?style=flat) ![pydantic](https://img.shields.io/badge/pydantic-%E2%89%A52.0.0-e92063?style=flat) ![netifaces](https://img.shields.io/badge/netifaces-%E2%89%A50.11.0-orange?style=flat) ![requests](https://img.shields.io/badge/requests-%E2%89%A52.31.0-blue?style=flat) ![pillow](https://img.shields.io/badge/pillow-%E2%89%A510.0.0-yellow?style=flat)

**Dual-protocol support with modern async/await architecture for seamless printer control and monitoring**

</div>

---

<div align="center">

## Features

| Capability | Details |
| --- | --- |
| **Dual Protocol Support** | Modern HTTP REST API for Adventurer 5M/5X series • Legacy TCP G-code protocol for all networked FlashForge printers |
| **Printer Discovery** | Automatic UDP broadcast discovery • Returns printer name, serial number, and IP address |
| **Full Control** | Movement and homing • Temperature control • Fan speed adjustment • LED lighting • Camera control • Air filtration system |
| **Real-time Monitoring** | Printer status and machine state • Current and target temperatures • Print progress and layer tracking • Estimated time remaining |
| **Job Management** | Start, pause, resume, and cancel print jobs • Progress monitoring |
| **File Operations** | List, upload, and download files • Extract print thumbnails • File metadata retrieval |
| **Async Architecture** | Native async/await implementation • Non-blocking network operations • Concurrent operations support |
| **Type Safety** | Full type hints for IDE autocomplete • Pydantic models for data validation • mypy strict mode compatible |
| **Model Detection** | Automatic capability detection • Feature flags for model-specific functions • Graceful degradation for older models |

</div>

---

<div align="center">

## Supported Printers

| Model | Support Level | Protocols | Features |
| --- | --- | --- | --- |
| **FlashForge Adventurer 5M** | Full Support | HTTP + TCP | All features including LED, camera, filtration |
| **FlashForge Adventurer 5M Pro** | Full Support | HTTP + TCP | All features including advanced filtration control |
| **FlashForge Adventurer 5X** | Full Support | HTTP + TCP | All features with multi-material support |
| **FlashForge Adventurer 3 / 4** | Partial Support | TCP Only | Basic control, temperature, movement, status |
| **Other (Network-enabled)** | Experimental | TCP Only | Generic G-code commands, may vary by model |

</div>

---

<div align="center">

## Installation

| Method | Command |
| --- | --- |
| **PyPI (Recommended)** | `pip install flashforge-python-api` |
| **Development Install** | `pip install -e ".[dev]"` |
| **With Imaging Support** | `pip install flashforge-python-api[imaging]` |
| **All Optional Dependencies** | `pip install flashforge-python-api[all]` |

</div>

---

## Quick Start

<div align="center">

**Important: LAN-Only Mode Required**

Your printer must be in **LAN-only mode** to communicate with this library. See the [official FlashForge guide](https://wiki.flashforge.com/en/Orca-Flashforge-and-Flashmaker/orca-flashforge-quick-start-guide#connect-via-lan-only-mode) for setup instructions and to obtain your check code.

</div>

### Printer Discovery

Discover FlashForge printers on your local network automatically:

```python
from flashforge import FlashForgePrinterDiscovery
import asyncio

async def discover():
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()

    for printer in printers:
        print(f"Found: {printer.name} at {printer.ip_address}")
        print(f"Serial: {printer.serial_number}")

asyncio.run(discover())
```

### Basic Printer Control

Connect to a printer and perform basic operations:

```python
from flashforge import FlashForgeClient
import asyncio

async def control_printer():
    # Initialize client with printer credentials
    client = FlashForgeClient("192.168.1.100", "SERIAL_NUMBER", "CHECK_CODE")

    # Always initialize before operations
    if await client.initialize():
        print(f"Connected to {client.printer_name}")
        print(f"Firmware: {client.firmware_version}")

        # Set temperatures
        await client.temp_control.set_bed_temp(60)
        await client.temp_control.set_extruder_temp(220)

        # Home all axes
        await client.control.home_xyz()

        # Turn on LED lights (AD5M/5X only)
        if client.is_ad5x:
            await client.control.set_led_on()

        # Clean up
        await client.dispose()

asyncio.run(control_printer())
```

### Real-time Status Monitoring

Monitor printer status, temperatures, and print progress:

```python
from flashforge import FlashForgeClient
import asyncio

async def monitor_printer():
    async with FlashForgeClient("192.168.1.100", "SERIAL", "CODE") as client:
        # Get comprehensive status via HTTP
        status = await client.get_printer_status()
        print(f"State: {status.machine_state}")
        print(f"Progress: {status.print_progress}%")

        # Get real-time temperatures via TCP
        temps = await client.tcp_client.get_temp_info()
        if temps:
            bed = temps.get_bed_temp()
            extruder = temps.get_extruder_temp()
            print(f"Bed: {bed.get_current()}°C / {bed.get_target()}°C")
            print(f"Extruder: {extruder.get_current()}°C / {extruder.get_target()}°C")

        # Check print progress via TCP
        layer_p, sd_p, current_layer = await client.tcp_client.get_print_progress()
        print(f"Layer Progress: {layer_p}% (Layer {current_layer})")

asyncio.run(monitor_printer())
```

### File Operations and Thumbnails

List files and extract G-code thumbnails:

```python
from flashforge import FlashForgeClient
import asyncio

async def file_operations():
    async with FlashForgeClient("192.168.1.100", "SERIAL", "CODE") as client:
        # List all files on printer
        files = await client.files.get_file_list()
        print(f"Found {len(files)} files")

        for filename in files:
            print(f"\nFile: {filename}")

            # Extract thumbnail image
            thumb = await client.tcp_client.get_thumbnail(filename)
            if thumb and thumb.has_image_data():
                print(f"Thumbnail: {len(thumb.get_image_bytes())} bytes")

                # Save thumbnail to disk
                thumb.save_to_file_sync(f"{filename}.png")
                print(f"Saved thumbnail as {filename}.png")

asyncio.run(file_operations())
```

---

<div align="center">

## Documentation

| Resource | Description |
| --- | --- |
| **[Client API Reference](docs/client.md)** | Complete API reference for `FlashForgeClient` and all control modules |
| **[Data Models](docs/models.md)** | Pydantic model documentation for status objects and responses |
| **[Protocols (HTTP/TCP)](docs/protocols.md)** | Understanding the dual-protocol architecture and when to use each |
| **[Advanced Usage](docs/advanced.md)** | Async patterns, error handling, concurrent operations, and best practices |
| **[Complete API Reference](docs/api_reference.md)** | Full class hierarchy and method listing |

</div>

---

<div align="center">

## Development

| Task | Command | Description |
| --- | --- | --- |
| **Setup Environment** | `python -m venv .venv && .venv\Scripts\activate` | Create and activate virtual environment |
| **Install Dependencies** | `pip install -e ".[dev]"` | Install package with development tools |
| **Run Tests** | `pytest` | Execute test suite |
| **Type Check** | `mypy flashforge/` | Run strict type checking with mypy |
| **Format Code** | `black flashforge/ tests/` | Format code with Black (line length: 100) |
| **Lint** | `ruff check flashforge/ tests/` | Lint code with Ruff |
| **Coverage Report** | `pytest --cov=flashforge --cov-report=html` | Generate test coverage report |
| **Build Package** | `python -m build` | Build distribution packages |
| **Run Pre-commit** | `pre-commit run --all-files` | Execute all pre-commit hooks |

</div>

---

<div align="center">

## License

**MIT License** - See [LICENSE](LICENSE) for details

</div>

