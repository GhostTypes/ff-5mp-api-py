<div align="center">

# FlashForge API Documentation

**Comprehensive guide to controlling FlashForge 3D printers with Python**

![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=flat) ![Documentation](https://img.shields.io/badge/Documentation-Complete-brightgreen?style=flat) ![Status](https://img.shields.io/badge/Status-Stable-brightgreen?style=flat)

**Everything you need to integrate FlashForge printer control into your Python applications**

</div>

---

<div align="center">

## Documentation Navigation

| Guide | Description |
| --- | --- |
| **[Client API Reference](client.md)** | Complete API reference for `FlashForgeClient`, `FlashForgePrinterDiscovery`, and all control modules (movement, temperature, jobs, files) |
| **[Data Models](models.md)** | Pydantic model documentation for `FFMachineInfo`, `Temperature`, `MachineState`, and all response objects with field descriptions |
| **[Protocols (HTTP/TCP)](protocols.md)** | Understanding the dual-protocol architecture • When to use HTTP vs TCP • Command structure and response formats |
| **[Advanced Usage](advanced.md)** | Async/await patterns • Error handling strategies • Concurrent operations • Type hints and safety • G-code thumbnails |
| **[Complete API Reference](api_reference.md)** | Full class hierarchy and method listing • Module organization • Quick lookup for all available functions |

</div>

---

<div align="center">

## Quick Reference

| Task | API Method | Protocol |
| --- | --- | --- |
| **Discover Printers** | `FlashForgePrinterDiscovery().discover_printers_async()` | UDP Broadcast |
| **Get Printer Status** | `client.get_printer_status()` | HTTP |
| **Read Temperatures** | `client.tcp_client.get_temp_info()` | TCP (M105) |
| **Set Bed Temperature** | `client.temp_control.set_bed_temp(temp)` | HTTP |
| **Set Nozzle Temperature** | `client.temp_control.set_extruder_temp(temp)` | HTTP |
| **Home All Axes** | `client.control.home_xyz()` | HTTP |
| **Pause Print** | `client.job_control.pause_print_job()` | HTTP |
| **Resume Print** | `client.job_control.resume_print_job()` | HTTP |
| **Cancel Print** | `client.job_control.cancel_print_job()` | HTTP |
| **List Files** | `client.files.get_file_list()` | TCP |
| **Get Print Progress** | `client.tcp_client.get_print_progress()` | TCP (M27) |
| **Extract Thumbnail** | `client.tcp_client.get_thumbnail(filename)` | TCP (M662) |
| **Control LED** | `client.control.set_led_on()` / `set_led_off()` | HTTP (AD5M/5X) |
| **Control Camera** | `client.control.turn_camera_on()` / `turn_camera_off()` | HTTP (Pro) |

</div>

---

<div align="center">

## Getting Started

| Step | Instructions |
| --- | --- |
| **1. Installation** | `pip install flashforge-python-api` |
| **2. Basic Setup** | Import `FlashForgeClient` and `FlashForgePrinterDiscovery` from `flashforge` package |
| **3. Discover Printer** | Use `FlashForgePrinterDiscovery` to find printers on your network |
| **4. Initialize Client** | Create `FlashForgeClient(ip, serial, check_code)` and call `await client.initialize()` |
| **5. Start Controlling** | Access control modules via `client.control`, `client.temp_control`, `client.job_control`, etc. |

</div>

---

## Basic Example

Minimal example to get started with printer control:

```python
import asyncio
from flashforge import FlashForgePrinterDiscovery, FlashForgeClient

async def main():
    # 1. Discover printers on network
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()

    if not printers:
        print("No printers found")
        return

    printer = printers[0]
    print(f"Found: {printer.name} at {printer.ip_address}")

    # 2. Connect to printer
    client = FlashForgeClient(printer.ip_address, printer.serial_number, "")

    if await client.initialize():
        # 3. Get status
        status = await client.get_printer_status()
        print(f"Status: {status.machine_state}")
        print(f"Bed: {status.print_bed.current}°C / {status.print_bed.set}°C")
        print(f"Nozzle: {status.extruder.current}°C / {status.extruder.set}°C")

        # 4. Clean up
        await client.dispose()

asyncio.run(main())
```

---

<div align="center">

## Key Concepts

| Concept | Explanation |
| --- | --- |
| **Dual Protocol** | Library uses both HTTP (modern REST-like API) and TCP (legacy G-code) depending on operation and printer model |
| **Async Architecture** | All network operations are async/await based for non-blocking I/O and efficient concurrent operations |
| **Model Detection** | Client automatically detects printer capabilities (`is_ad5x`, `is_pro`) based on model name to enable/disable features |
| **Type Safety** | Pydantic models validate all responses and provide type-safe access with IDE autocomplete support |
| **Control Modules** | Functionality is organized into specialized modules: `control`, `job_control`, `temp_control`, `files`, `info` |
| **Context Manager** | Client supports `async with` for automatic connection management and cleanup |

</div>

---

<div align="center">

## Supported Operations

| Category | Operations |
| --- | --- |
| **Discovery** | UDP broadcast discovery • Manual IP connection • Serial number extraction |
| **Status & Info** | Machine state • Firmware version • Printer name • MAC address • Full status object |
| **Temperature** | Read current/target temps (M105) • Set bed temperature • Set nozzle temperature • Cooldown all heaters |
| **Movement** | Home axes (G28) • Move to position (G1) • Relative/absolute positioning |
| **Print Jobs** | Start print • Pause print • Resume print • Cancel print • Monitor progress |
| **File Management** | List files on printer • Upload G-code files • Download files • Delete files • Extract thumbnails |
| **Camera & Lights** | LED control (AD5M/5X) • Camera on/off (Pro models) • Get camera stream URL |
| **Fans & Filtration** | Chamber fan speed • Cooling fan speed • Internal/external filtration control |
| **Endstops** | Read endstop status (M119) • Monitor limit switches |
| **Advanced** | Direct G-code execution • Raw TCP commands • Custom HTTP requests |

</div>

---

<div align="center">

## Hardware Compatibility

| Printer Model | HTTP Support | TCP Support | Special Features |
| --- | --- | --- | --- |
| **Adventurer 5M** | Full | Full | LED, Camera, Basic Filtration |
| **Adventurer 5M Pro** | Full | Full | LED, Camera, Advanced Filtration |
| **Adventurer 5X** | Full | Full | LED, Camera, Multi-Material |
| **Adventurer 3** | Limited | Full | Basic G-code only |
| **Adventurer 4** | Limited | Full | Basic G-code only |
| **Other Models** | Varies | Experimental | Generic G-code commands |

</div>

---

<div align="center">

## External Resources

| Resource | Link |
| --- | --- |
| **PyPI Package** | [flashforge-python-api](https://pypi.org/project/flashforge-python-api/) |
| **GitHub Repository** | [GhostTypes/ff-5mp-api-py](https://github.com/GhostTypes/ff-5mp-api-py) |
| **Report Issues** | [GitHub Issues](https://github.com/GhostTypes/ff-5mp-api-py/issues) |
| **Main README** | [Project README](../README.md) |

</div>

---

<div align="center">

## Need Help?

| Question Type | Recommended Resource |
| --- | --- |
| **How do I use a specific feature?** | Check [Client API Reference](client.md) for detailed method documentation |
| **What data does a response contain?** | See [Data Models](models.md) for all Pydantic model field descriptions |
| **When should I use HTTP vs TCP?** | Read [Protocols Guide](protocols.md) for protocol decision matrix |
| **How do I handle errors or use async?** | Review [Advanced Usage](advanced.md) for patterns and best practices |
| **What methods are available?** | Browse [Complete API Reference](api_reference.md) for full class hierarchy |

</div>

---

<div align="center">

**Ready to get started? Begin with the [Client API Reference](client.md)**

</div>
