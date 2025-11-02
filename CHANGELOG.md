# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.0
