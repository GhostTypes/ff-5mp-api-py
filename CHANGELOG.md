# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.2]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.2
[1.0.1]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.1
[1.0.0]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.0
