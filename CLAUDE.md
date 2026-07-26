# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FlashForge Python API is a comprehensive Python library for controlling FlashForge 3D printers. The library provides **dual-protocol** support:
- **HTTP API**: Modern REST-like API for Adventurer 5M/5X and Creator 5 series printers
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
   - Automatically detects printer capabilities (is_ad5x, is_pro, is_creator5, is_creator5_pro) based on model

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
│   │   ├── temp_control.py     # TempControl class
│   │   └── creator5_palette.py # Creator 5 material-station palette (CIEDE2000)
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

**Model Detection**: `MachineInfoParser.from_detail()` derives `is_pro` / `is_ad5x` / `is_creator5` / `is_creator5_pro` on `FFMachineInfo` from the firmware-set integer `pid` field on `/detail` (35 = Adventurer 5M, 36 = 5M Pro, 38 = AD5X, plus Creator 5 / Creator 5 Pro PIDs — see `KNOWN_HTTP_PIDS` and the `PID_*` constants in `flashforge/api/controls/info.py`). The `pid` value is also passed through to `FFMachineInfo.pid` for downstream consumers. When `pid` is absent (older firmware) the parser falls back to a name+capability heuristic, but new code should NOT rely on substring-matching `detail.name` — that field is user-mutable via the printer's LCD or cloud account and changing it broke detection in pre-1.2.3 builds (see CHANGELOG entry for 1.2.3, ref `ff-5mp-hass#13`). The Creator 5 series is **HTTP-only**: it exposes no TCP/8899 service, so `client._http_only` is true and the client routes temperature control through the HTTP `temperatureCtl_cmd` instead of TCP M105.

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

**IMPORTANT**: Releases are managed through GitHub Actions workflow, not manual PyPI uploads.

#### Release Process (Production)

1. **Prepare the release locally:**
   ```bash
   # Update version in pyproject.toml (e.g., 1.0.2 -> 1.0.3)
   # Update CHANGELOG.md with new version section and changes

   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to X.Y.Z"
   git push
   ```

2. **Trigger GitHub Actions workflow:**
   - Go to: https://github.com/GhostTypes/ff-5mp-api-py/actions
   - Click "Publish Release" workflow
   - Click "Run workflow" button
   - Enter version number (e.g., `1.0.3`)
   - Click green "Run workflow" button

3. **Workflow automatically:**
   - Validates version format (X.Y.Z)
   - Verifies version in `pyproject.toml` matches input
   - Checks tag doesn't already exist
   - Creates and pushes git tag `vX.Y.Z`
   - Builds package with Hatchling
   - Verifies build with `twine check`
   - Creates GitHub Release with auto-generated changelog
   - Publishes to PyPI using `PYPI_API_TOKEN` secret

#### PyPI Authentication

Publishing uses GitHub Secrets (not `.pypirc`):
- **Secret name**: `PYPI_API_TOKEN`
- **Location**: Repository Settings → Secrets and variables → Actions
- **Format**: PyPI API token (starts with `pypi-`)
- **Fallback**: Workflow gracefully skips PyPI upload if secret not configured

#### Manual Building (Development/Testing)

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build package
python -m build

# Check distribution
twine check dist/*

# DO NOT manually upload to PyPI - use workflow instead
```

**Version Management**:
- Current version: **1.3.3** (as of 2026-07-26)
- Package name: `flashforge-python-api`
- PyPI: https://pypi.org/project/flashforge-python-api/
- Build system: Hatchling (defined in `pyproject.toml`)

#### Important Notes

- **Never manually upload to PyPI** - always use the GitHub Actions workflow
- **Always update CHANGELOG.md** before releasing - workflow doesn't auto-generate it
- **Version must match** between `pyproject.toml` and workflow input or it will fail
- **Tags are permanent** - workflow prevents duplicate tags
- **Linear history required** - workflow creates tags on current HEAD, no version bump commits

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
- **Per-nozzle & chamber temperature control, material-station slot configuration / color mapping**: Creator 5 / Creator 5 Pro only (HTTP `temperatureCtl_cmd`; slot colors snap to the firmware palette via CIEDE2000 in `api/controls/creator5_palette.py`)

Capability flags (`client.is_pro`, `client.is_ad5x`, `client.is_creator5`, `client.is_creator5_pro`) are populated from `FFMachineInfo` after `verify_connection()`, which itself reads `pid` off `/detail`. Trust those flags — do not re-derive them from `info.name`.

**Never surface a raw `/detail` field as a capability flag, and never give a capability an "unknown" state.** Firmware omits fields that don't apply to a model, so an absent value means "not reported", not "no" — and any type that can hold `None` invites a consumer to read the two as the same thing. `hasMatlStation` is the known case: it is AD5X-only, and a Creator 5 Pro leaves it out of `/detail` entirely (verified on firmware 1.9.4) while reporting a fully populated `matlStationInfo` with four loaded slots. `FFMachineInfo.has_matl_station` is therefore **derived** in `MachineInfoParser.from_detail` (flag `is True` OR `slot_cnt > 0` OR non-empty `slot_infos`) and typed `bool`, not `bool | None`; the raw value stays on `FFPrinterDetail`. The same trap caught `led_control_override` downstream, where a caller's unset `False` was read as "force the capability off". Apply the rule to any new capability: derive it from the data the capability actually produces, give it no unknown state, and cover it with a fixture built from a real payload — the Creator 5 fixtures originally had no material station at all, which is why this went unnoticed through v1.3.1.

**The rule for response models: `extra="allow"` on anything parsed from a printer response, `extra="forbid"` on anything this library constructs itself.** A model that forbids unknown fields turns a firmware addition into a parse failure, and every parse failure here degrades into something that looks like a working printer with less to report — or worse. `ff-5mp-hass#18` is the canonical case: `Product` forbade extras, so an unrecognized control-state flag raised `ValidationError`, `send_product_command` returned the same bare `False` it returns for bad credentials, and the user was told their check code was wrong when it was not.

Two things this rule is easy to get half-right:

1. **It applies to nested models, not just the top-level response.** A child that forbids extras fails validation for the entire response, so `FFPrinterDetail` being `extra="allow"` bought nothing while `MatlStationInfo` / `SlotInfo` / `IndepMatlInfo` underneath it still forbade them. Every model reachable from a parsed payload has to allow extras, all the way down.
2. **The inverse half is load-bearing — do not strip `extra="forbid"` indiscriminately.** Outbound request-parameter models (`AD5XLocalJobParams`, `Creator5UploadParams`, `FilamentArgs`, …) are request bodies *we* build, so no firmware update can break them, and forbidding extras turns a caller's typo'd keyword into an error instead of a field the printer silently ignores. Same for `FFMachineInfo` and `Temperature`, which are only ever constructed by `MachineInfoParser.from_detail` from keyword arguments — there, forbidding extras is a typo check on our own parser.

The one cost of `extra="allow"` on inbound models: a typo'd `alias=` stops raising and silently becomes an extra field. Keep asserting on parsed *values* in fixtures rather than just successful construction, which is what still catches it.

### Why TCP Bootstrap Is Still Required for Modern Printers
The HTTP `/detail` endpoint requires authentication (`serialNumber` + `checkCode` via `FNetCode`). During discovery and the very first connection attempt — before a check code has been entered — there are no credentials, so the parser cannot read `pid` from `/detail`. The library handles this by:

1. Discovery (UDP) returns the printer's USB-style PID in the broadcast packet, which `discovery/discovery.py` already maps to a `PrinterModel`. Consumers can use this to pre-select a model class before pairing.
2. After a check code is provided, `client.initialize()` performs both an authenticated `/detail` call and an unauthenticated TCP `M115` (`tcp_client.get_printer_info()`). The TCP `M115` response carries `Machine Type` (firmware-controlled, e.g. `"FlashForge Adventurer 5M Pro"`) which is safe to substring-match for capability inference; do NOT use the M115 `Machine Name` field for that — like `detail.name` it is user-set.
3. Once `verify_connection()` finishes, `FFMachineInfo.pid` / `is_pro` / `is_ad5x` are authoritative. All later capability gating should read those, not re-parse strings.

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
- FlashForge AD5X
- FlashForge Adventurer 5M / 5M Pro
- FlashForge Adventurer 4

**Full Support** (HTTP only — no TCP/8899 service):
- FlashForge Creator 5
- FlashForge Creator 5 Pro

**Partial Support** (TCP only):
- FlashForge Adventurer 3

## Dependencies

**Core runtime** (required):
- `aiohttp>=3.8.0` - Async HTTP client
- `pydantic>=2.0.0` - Data validation and models
- `ifaddr>=0.2.0` - Pure-Python network interface enumeration for discovery
- `requests>=2.31.0` - Sync HTTP (used in some utilities)

**Development** (optional `[dev]`):
- `pytest>=7.0.0`, `pytest-asyncio>=0.21.0`, `pytest-cov>=4.0.0`
- `black>=23.0.0`, `ruff>=0.1.0`, `mypy>=1.0.0`
- `pre-commit>=3.0.0`

**Imaging** (optional `[imaging]`):
- `pillow>=10.0.0` - For thumbnail image processing

**Python version**: Requires Python 3.11+

## Common Gotchas

### Client Usage
1. **Always call `await client.initialize()`** before using the main FlashForgeClient (sets up HTTP session)
2. **Model detection** depends on printer name response - early operations may not have full capability info
3. **TCP keep-alive** runs as background task - call `dispose()` or use context manager to clean up
4. **Temperature queries** via TCP (`client.tcp_client.get_temp_info()`) return parsed objects, not raw values
5. **Thumbnail extraction** (M662) can be slow and returns large payloads - use with caution
6. **File uploads** for AD5X models have different parameters than older models (see `AD5XUploadParams`)

### Release Workflow
7. **Version bump must be manual** - Workflow does NOT automatically update `pyproject.toml` or `CHANGELOG.md`
8. **Workflow validates version match** - Input version must exactly match version in `pyproject.toml` or it fails
9. **No timestamped versions** - Previous workflow created orphaned commits with timestamp versions (e.g., `v1.0.0-20251122005123`) which caused duplicate changelogs. Current workflow uses clean tags only
10. **Changelog duplication** - If you see duplicate PRs in GitHub release notes, it means there's a tag on an orphaned commit outside the main branch lineage. Delete the orphaned tag to fix
11. **Linear git history required** - Workflow creates tags on current HEAD without making commits. All version bumps must be committed to `main` before running workflow
12. **PyPI token is required** - Without `PYPI_API_TOKEN` secret, workflow completes but skips PyPI upload
