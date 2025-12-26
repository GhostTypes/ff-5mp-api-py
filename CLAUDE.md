# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FlashForge Python API is a comprehensive Python library for controlling FlashForge 3D printers. The library provides **dual-protocol** support:
- **HTTP API**: Modern REST-like API for Adventurer 5M/5X series printers
- **TCP/G-code API**: Legacy protocol supporting all networked FlashForge printers

The architecture is fully async/await throughout and uses Pydantic for type-safe data models.

## Core Architecture

### Client Layer Hierarchy

The library has a layered client architecture:

1. **`flashforge.client.FlashForgeClient`** (Main unified client at `flashforge/client.py`)
   - The primary user-facing API that orchestrates both HTTP and TCP communication
   - Manages HTTP session (aiohttp) for modern API endpoints
   - Contains a `tcp_client` instance for legacy operations
   - Provides 5 control modules:
     - `control`: Movement, LED, filtration, camera operations
     - `job_control`: Print job management
     - `info`: Status and machine information
     - `files`: File operations (upload/download/list)
     - `temp_control`: Temperature settings
   - Automatically detects printer capabilities (is_ad5x, is_pro) based on model

2. **`flashforge.tcp.ff_client.FlashForgeClient`** (TCP high-level client)
   - Extends `FlashForgeTcpClient`
   - Implements G-code/M-code command workflows
   - Used internally by the main client's TCP operations
   - Contains `GCodeController` instance for command execution

3. **`flashforge.tcp.tcp_client.FlashForgeTcpClient`** (TCP low-level client)
   - Base TCP communication layer managing socket connections
   - Handles raw command sending/receiving
   - Maintains keep-alive connections
   - Default port: 8899, timeout: 5.0s

### Module Organization

```
flashforge/
├── client.py                    # Main FlashForgeClient (HTTP + TCP orchestrator)
├── discovery/                   # UDP-based printer discovery
│   └── discovery.py            # FlashForgePrinterDiscovery
├── tcp/                        # TCP/G-code protocol implementation
│   ├── tcp_client.py           # Low-level TCP socket management
│   ├── ff_client.py            # High-level G-code client
│   ├── gcode/                  # G-code command definitions and controller
│   │   ├── gcodes.py           # GCodes enum with all commands
│   │   └── gcode_controller.py # GCodeController for executing commands
│   └── parsers/                # Response parsers for TCP commands
│       ├── temp_info.py        # M105 temperature parsing
│       ├── printer_info.py     # M115 printer info parsing
│       ├── thumbnail_info.py   # M662 thumbnail extraction
│       ├── endstop_status.py   # M119 endstop parsing
│       ├── location_info.py    # M114 position parsing
│       └── print_status.py     # M27 print progress parsing
├── api/                        # HTTP API implementation
│   ├── constants/              # Command and endpoint definitions
│   │   ├── commands.py         # Commands enum
│   │   └── endpoints.py        # Endpoints class
│   ├── controls/               # Control modules (used by main client)
│   │   ├── control.py          # Control class
│   │   ├── job_control.py      # JobControl class
│   │   ├── info.py             # Info class
│   │   ├── files.py            # Files class (named 'files' for user API)
│   │   └── temp_control.py     # TempControl class
│   ├── network/                # Network utilities
│   │   ├── utils.py            # NetworkUtils for HTTP requests
│   │   └── fnet_code.py        # FNetCode for authentication
│   ├── filament/               # Filament handling
│   └── misc/                   # Utilities (temperature, scientific notation)
└── models/                     # Pydantic models for API responses
    ├── responses.py            # All HTTP response models
    └── machine_info.py         # Machine state and info models
```

### Key Design Patterns

**Dual Protocol Strategy**: HTTP is used for high-level operations (printer status, file listing, job control commands) while TCP/G-code is used for real-time operations (temperature monitoring via M105, print progress via M27, thumbnails via M662).

**Model Detection**: The client sets `_is_ad5x` flag by checking printer name for "5M" or "5X" which enables/disables certain API features (LED control, camera, filtration).

**Parser Pattern**: TCP responses are parsed by specialized parser classes in `tcp/parsers/` that extract structured data from text responses (e.g., `M105` returns text like `T0:25/0 T1:25/0 B:25/0` which TempInfo parses).

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"
# Or install all optional dependencies:
pip install -e ".[all]"
```

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=flashforge --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_parsers.py

# Run tests matching pattern
pytest -k "test_temp"

# Skip slow/integration tests
pytest -m "not slow and not integration"

# Run only network tests
pytest -m network

# Alternative: Use the test runner script
python tests/run_tests.py
```

### Code Quality
```bash
# Format code with Black (line length: 100)
black flashforge/ tests/

# Lint with Ruff
ruff check flashforge/ tests/

# Type check with mypy (strict mode enabled)
mypy flashforge/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Building & Publishing

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build package
python -m build

# Check distribution
twine check dist/*

# Upload to PyPI (credentials from .pypirc)
python -m twine upload dist/*
```

**Version Management**:
- Current version: **1.0.1** (as of 2025-12-24)
- Update version in `pyproject.toml` before publishing
- Package name: `flashforge-python-api`
- PyPI: https://pypi.org/project/flashforge-python-api/

### PyPI Publishing Configuration

The project uses `.pypirc` in the root directory for PyPI authentication:
- File contains PyPI username and API token
- Git-ignored (never committed)
- Automatically read by twine during `python -m twine upload dist/*`
- Build system: Hatchling (defined in `pyproject.toml`)

## Testing Strategy

### Test Organization
- **Unit tests**: `test_parsers.py`, `test_utility_classes.py` - Test individual components
- **Integration tests**: `test_ad5x_live_integration.py`, `test_5m_pro_live_integration.py` - Require actual printer
- **Component tests**: `test_client.py`, `test_control.py`, etc. - Test control modules

### Test Configuration
- pytest config in `pyproject.toml` under `[tool.pytest.ini_options]`
- Markers: `slow`, `integration`, `network`
- Async mode: `auto` (pytest-asyncio)
- Test fixtures in `tests/fixtures/` and `tests/conftest.py`
- Printer configuration: `tests/printer_config.py` (for live tests)

### Running Integration Tests
Live integration tests require:
1. A networked FlashForge printer
2. Printer credentials (IP, serial, check code) configured in `tests/printer_config.py`
3. Mark tests with `@pytest.mark.integration` or `@pytest.mark.network`

## Important Implementation Details

### HTTP vs TCP Decision Matrix
- **Use HTTP for**: Status queries (`get_printer_status`), file listing, job control (start/pause/cancel), printer info
- **Use TCP for**: Real-time temperature (`M105`), print progress (`M27`), endstops (`M119`), thumbnails (`M662`), direct G-code

### Authentication & Connection
- HTTP requires: IP address, serial number, check code
- HTTP endpoint construction: `http://{ip}:{port}/...` (port 8898)
- HTTP auth via `FNetCode.generate()` adds `fnetCode` and `serialNumber` to requests
- TCP only requires IP (port 8899), no auth

### Async Pattern
All API methods are async and should be awaited:
```python
async with FlashForgeClient(ip, serial, check) as client:
    await client.initialize()  # Required for HTTP session setup
    status = await client.get_printer_status()
    await client.dispose()  # Or use context manager
```

### Type Safety
- Pydantic models in `models/responses.py` validate all API responses
- Recent fix (v1.0.1): `estimated_time` changed from `int` to `float` for validation
- Mypy strict mode enabled - all functions must have type hints

### Model-Specific Features
Certain features only work on specific models:
- **LED control**: Adventurer 5M/5X only (check `client.led_control`)
- **Filtration**: Adventurer 5M Pro only (check `client.filtration_control`)
- **Camera**: Detected via model name (check `client.is_ad5x`)

### Error Handling
- HTTP errors: Wrapped in aiohttp exceptions
- TCP errors: Socket timeouts, connection refused
- Parser errors: Invalid response formats from TCP commands
- Always check `client.initialize()` return value before operations

## Documentation

- Main docs in `docs/` directory:
  - `README.md`: Documentation overview
  - `client.md`: FlashForgeClient API reference
  - `models.md`: Pydantic model descriptions
  - `protocols.md`: HTTP vs TCP protocol details
  - `advanced.md`: Advanced usage patterns
  - `api_reference.md`: Complete API listing

- Examples in `examples/`:
  - `discovery_example.py`: Printer discovery usage
  - `tcp_client_example.py`: Direct TCP client usage
  - `unified_client_example.py`: Main client usage
  - `complete_feature_demo.py`: Comprehensive feature demonstration

## Supported Hardware

**Full Support** (HTTP + TCP):
- FlashForge Adventurer 5M / 5M Pro
- FlashForge Adventurer 5X

**Partial Support** (TCP only):
- FlashForge Adventurer 3 / 4
- Other networked FlashForge printers (experimental)

## Dependencies

**Core runtime** (required):
- `aiohttp>=3.8.0` - Async HTTP client
- `pydantic>=2.0.0` - Data validation and models
- `netifaces>=0.11.0` - Network interface enumeration for discovery
- `requests>=2.31.0` - Sync HTTP (used in some utilities)

**Development** (optional `[dev]`):
- `pytest>=7.0.0`, `pytest-asyncio>=0.21.0`, `pytest-cov>=4.0.0`
- `black>=23.0.0`, `ruff>=0.1.0`, `mypy>=1.0.0`
- `pre-commit>=3.0.0`

**Imaging** (optional `[imaging]`):
- `pillow>=10.0.0` - For thumbnail image processing

**Python version**: Requires Python 3.8+

## Common Gotchas

1. **Always call `await client.initialize()`** before using the main FlashForgeClient (sets up HTTP session)
2. **Model detection** depends on printer name response - early operations may not have full capability info
3. **TCP keep-alive** runs as background task - call `dispose()` or use context manager to clean up
4. **Temperature queries** via TCP (`client.tcp_client.get_temp_info()`) return parsed objects, not raw values
5. **Thumbnail extraction** (M662) can be slow and returns large payloads - use with caution
6. **File uploads** for AD5X models have different parameters than older models (see `AD5XUploadParams`)
