# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-03-21

### Added

- `CAMERA_STREAM_PORT` - exported constant for the known FlashForge OEM MJPEG stream port
- `FlashForgeClient.detect_camera_stream()` - probes `http://<printer-ip>:8080/?action=stream` and falls back from `HEAD` to `GET` when firmware does not report `camera_stream_url`
- Pytest coverage for camera stream probing success, `HEAD` timeout fallback, and no-camera behavior
- `FlashForgeA4Client` - dedicated Adventurer 4 Lite / Pro TCP client aligned with the documented M601 and M115 protocol behavior
- `A4BuildVolume`, `A4FileEntry`, and `A4PrinterInfo` for typed Adventurer 4 responses

### Changed

- Discovery PID fallback now recognizes Adventurer 4 Lite (`0x0016`) as well as Adventurer 4 Pro (`0x001E`)
- README guidance now points Adventurer 3 / 4 users at the dedicated TCP clients instead of only the generic legacy layer

## [1.1.1] - 2026-03-09

### Fixed

- Fixed AD5X `/detail` response parsing for newer firmware fields including `camera`, `clearFanStatus`, `coordinate`, `extrudeCtrl`, and `moveCtrl`
- Made raw printer detail parsing tolerant of additional future firmware fields instead of failing validation
- Added regression coverage for extended AD5X detail payloads

## [1.1.0] - 2026-03-08

### Added

- `FlashForgeA3Client` â€” full Adventurer 3 TCP client with dedicated G-code protocol support
- `A3GCodeController` â€” A3-specific G-code command controller
- `FlashForgeClient.camera_stream_url` â€” caches the OEM camera stream URL reported by the printer in machine-info responses
- `thumbnail_info` parser for handling printer thumbnail responses
- New G-code commands in `gcodes.py` for broader printer compatibility
- Test coverage for A3 client, camera stream URL caching, and machine-info model parity
- mypy exclude configuration for tests and examples

### Changed

- Major refactor of `discovery.py` for improved reliability and cross-printer compatibility
- `tcp_client.py` substantially reworked for better connection handling and parser coverage
- Parsers (`endstop_status`, `location_info`, `print_status`, `printer_info`, `temp_info`) updated for improved type safety and correctness
- `client.py` extended with camera stream URL caching from machine-info responses
- `control.py` updated with refined API surface
- `info.py` refactored for cleaner response handling
- Ruff linter configuration updated to use `[tool.ruff.lint]` table (ruff >=0.1.0 syntax)
- Package exports in `__init__.py` updated to include new A3 types and client
- TCP module exports updated to expose A3 client and controller

### Fixed

- Discovery reliability improvements from `discovery.py` refactor
- TCP client parser edge cases addressed across all response types

## [1.0.2] - 2025-12-26

### Added

- Added LAN-only mode requirement notice in README Quick Start section with link to official FlashForge documentation
- Added dependency badges for aiohttp, pydantic, netifaces, requests, and pillow to README header
- Added readme-generator skill for maintaining consistent documentation formatting
- Added comprehensive developer documentation sections to CLAUDE.md

### Changed

- Completely rewrote main README.md with modern centered table-based formatting
- Modernized docs/README.md as comprehensive documentation hub entry point
- Expanded CLAUDE.md from basic PyPI notes to comprehensive developer guide with architecture documentation
- Updated supported printers table with clearer protocol and feature breakdown
- Reorganized README with four detailed quick start examples (discovery, control, monitoring, files)
- Simplified release workflow to use linear git history instead of timestamp versioning
- Made version input required (X.Y.Z format) for releases

### Fixed

- Fixed release workflow changelog duplication issue caused by orphaned timestamped commits
- Fixed `format_time_from_seconds` function to properly handle float values for `estimated_time`

### Removed

- Removed redundant Architecture and Requirements sections from README
- Removed complex timestamp versioning logic from release workflow
- Deleted orphaned timestamped tag `v1.0.0-20251122005123`

## [1.0.1] - 2025-12-24

### Fixed

- Fixed Pydantic validation error for `estimated_time` field in `FFPrinterDetail` and `FFMachineInfo` models. Changed type from `int` to `float` to handle printer API responses that return fractional time values.

## [1.0.0] - 2025-01-02

### Added

- Initial release of FlashForge Python API
- HTTP API client for modern FlashForge printers
- TCP/G-code client for legacy communication
- UDP-based printer discovery service
- Comprehensive async/await support throughout
- Full type safety with Pydantic models
- Control modules:
- `Control` - Movement, LED, filtration, camera control
- `JobControl` - Print job management (start/pause/resume/cancel)
- `Info` - Status and machine information retrieval
- `Files` - File upload/download/management
- `TempControl` - Temperature settings
- Support for FlashForge Adventurer 5M Series and Adventurer 4
- Model-specific feature detection (LED, filtration, camera)
- Comprehensive error handling and logging
- Example scripts and documentation

### Documentation

- Complete README with usage examples
- API reference documentation
- Type hints for all public APIs
- Inline code documentation

[Unreleased]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.1.1
[1.0.2]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.2
[1.0.1]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.1
[1.0.0]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.0
