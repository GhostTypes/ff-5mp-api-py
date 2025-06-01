# 🖨️ FlashForge Python API

A comprehensive Python library for controlling FlashForge 3D printers.

## ✨ Features

- **🎮 Full Printer Control**: Movement, temperature, speed, LED, filtration, camera control
- **📋 Job Management**: Start, pause, resume, cancel prints, file upload and management  
- **📊 Real-time Monitoring**: Live status, temperature, progress, and machine state tracking
- **🔍 Network Discovery**: Automatic printer discovery via UDP broadcast
- **🔄 Dual Communication**: HTTP API (modern) + TCP G-code (legacy) support
- **🛡️ Type Safety**: Full type hints and Pydantic models for robust development
- **⚡ Async Support**: Native async/await support for all operations
- **🖼️ Advanced Features**: Thumbnail extraction, endstop monitoring, print progress tracking

## 🚀 Quick Start
> 💡 The "new" HTTP API requires LAN-mode, and a check code for authentication. [This](https://www.youtube.com/watch?v=krdEGccZuKo) video shows how to set up LAN-mode, and get the code.

```python
from flashforge import FlashForgeClient, FlashForgePrinterDiscovery

# Find printers on the network
discovery = FlashForgePrinterDiscovery()
printers = await discovery.discover_printers_async()

# Connect to your printer
client = FlashForgeClient(
    host="192.168.1.100",  # Your printer's IP
    serial="ABCD1234",     # Your printer's serial
    check_code="12345678"  # Your printer's check code
)

# Basic operations
await client.info.get_machine_status()  # Get printer status
await client.temp_control.set_bed_temp(60)  # Set bed temperature
await client.control.home_xyz()  # Home all axes
```

## 📦 Installation & Setup

```bash
# Clone the repository
git clone https://github.com/your-username/flashforge-python-api.git
cd flashforge-python-api

# Setup & Install
uv sync                    # Install core dependencies
uv sync --all-extras      # Install with all optional dependencies
```

## 🔧 Requirements

- **🐍 Python**: 3.8+ (recommended: 3.11+)
- **🖨️ Printer**: FlashForge with network connectivity
- **🌐 Network**: Printer and computer on same network for discovery
- **🔑 Credentials**: Printer serial number and check code

## 🎯 Supported Models

**✅ Tested with:**
- FlashForge Adventurer 5M Series
- FlashForge Adventurer 4

**💫 Should work with:**
- FlashForge printers with network connectivity
- Printers supporting HTTP API (new) and/or TCP G-code (legacy)

> 💡 **Note**: Some features (camera control, filtration) are model-specific and will be automatically detected.

## 🌟 Related Projects
- **💻 C# API (Windows)**: [ff-5mp-api](https://github.com/GhostTypes/ff-5mp-api)
- **🌐 TypeScript API (Cross-Platform)**: [ff-5mp-api-ts](https://github.com/GhostTypes/ff-5mp-api-ts)
- **🎨 FlashForgeUI (Electron, Cross-Platform)**: [FlashForgeUI-Electron](https://github.com/Parallel-7/FlashForgeUI-Electron)

