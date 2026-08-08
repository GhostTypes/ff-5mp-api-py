# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.5] - 2026-08-08

### Fixed

- **A paused Creator 5 Pro no longer reports as "unknown".** The printer sends `status: "pause"`, while the mapping only knew the documented `"pausing"` and `"paused"` — so every pause fell through to `MachineState.UNKNOWN`. In Home Assistant that is the one state that says nothing, and it appeared at exactly the wrong moment: the printer pauses itself when it detects a clog, so the sensor went blank precisely when the user needed to know why the print had stopped. Found in a Home Assistant log carrying 84 `Unknown machine status received: 'pause'` warnings over a single day (pid 41, firmware 1.9.4). `"pause"` now maps to `PAUSED`; `"paused"` still does, because firmware reporting one is no reason to drop the other.

- **`status: "downloading"` is mapped too.** Reported while a file is being transferred to the printer, and likewise unmapped until now. It maps to `BUSY` rather than to a new enum member on purpose: a consumer that pins this enum to a fixed list breaks when a member appears, and mapping onto an existing state cannot break anyone. (`ff-5mp-hass` is not such a consumer — its `device_class=ENUM` sensor derives its `options` from `MachineState` itself, so a new member would reach it for free.) A dedicated `DOWNLOADING` state is worth discussing on its merits; it is not a bugfix, and it does not belong in a patch release.

## [1.3.4] - 2026-07-26

### Fixed

- **A single out-of-range field no longer costs the caller the entire `/detail` response.** A Creator 5 with no heated chamber reports `chamberTemp: -108` — the firmware's "this sensor does not exist" sentinel, a sibling of the `-100` this library itself sends as `TEMP_OFF`. `FFPrinterDetail.chamber_temp` carried `ge=-50`, so that one value failed validation for the whole model, `get_detail_response` returned `None`, and `ff-5mp-hass` reported an unreachable printer. Three releases went into `ff-5mp-hass#18` on the assumption it was a network or credential problem. The temperature fields now map any value at or below `-50` to `None`, so "no sensor" reads as "not reported" rather than as a `-108 °C` reading or a hard failure; `MachineInfoParser` exposes this as the new `FFMachineInfo.has_chamber_sensor`, which consumers should gate chamber entities on instead of the Creator 5 model family (the chamber is an option within it, not a family trait).

- **Every remaining range constraint was removed from inbound models, not just the one that was reported.** Fixing `chamberTemp` alone would only have relocated the next outage: `tvoc`, `printSpeedAdjust`, `zAxisCompensation`, `fillAmount`, `remainingDiskSpace`, `nozzleCnt` and ~20 more each carried a `ge`/`le` that could fail the entire response on a firmware revision or an unusual state. Pydantic validates a model all-or-nothing, so a constraint on a field nobody reads is enough to take a consumer down. `FFPrinterDetail`, `Temperature`, `SlotInfo`, `MatlStationInfo`, `IndepMatlInfo`, `FFGcodeToolData`, and `FFGcodeFileEntry` now validate types but not value ranges. Outbound request models (`AD5X*Params`, `Creator5*Params`, `FilamentArgs`, `AD5XMaterialMapping`) keep their constraints, where a bad value is our own bug rather than a firmware difference. This matches the TypeScript client (`ff-5mp-api-ts`), which takes what it needs from a response and has never hit this class of failure.

- **Nested inbound models no longer fail the parent over a missing or unusual field.** `SlotInfo` required `hasFilament`, `materialColor`, `materialName`, and `slotId`, so one absent attribute on one slot failed the whole `/detail` response; all four are now defaulted. Its hex-color validator *raised* on anything that was not `#RRGGBB` or empty — it now normalizes (expanding `#RGB`, adding a missing `#`) and degrades to an empty string, because an unrecognized color should cost a swatch its color, not cost the caller every entity. `MatlStationInfo.slot_infos` carried `min_length=1`, which made an explicitly empty `slotInfos: []` — a station with nothing loaded — invalid, and `max_length=4`, which would have failed on any future larger station.

### Added

- **`FlashForgeResponseError`, so callers can tell "unreadable answer" from "no answer".** Every failure path returned `None`, which meant a schema mismatch was indistinguishable from an unreachable printer — the reason `ff-5mp-hass#18` spent three releases pointing its reporter at the network. `get_detail_response()` now *raises* when the printer answered with a body that failed validation, and still returns `None` when the request never got through. `info.get()` raises the same error when a validated payload cannot be converted into `FFMachineInfo`. The convenience wrappers (`is_printing`, `get_status`, `get_machine_state`) keep their documented fallback returns and absorb it, so only callers that asked for the distinction have to handle it.

- **`Info.get_detail_raw()`**, returning the decoded `/detail` JSON with no model validation. This lets a consumer read identity fields — above all `pid` — without first validating ~50 unrelated fields, so a supported printer can no longer be rejected because of a field that has nothing to do with whether it is supported.

- **`FFMachineInfo.has_chamber_sensor`**, set from whether the printer actually reported a chamber temperature.

### Changed

- **`__init__.py` reported `__version__ = "1.3.1"` while `pyproject.toml` said `1.3.3`.** Both now read `1.3.4`.

- **`CLAUDE.md`'s "Why TCP Bootstrap Is Still Required for Modern Printers" section described behavior the library deliberately does not have.** It claimed `client.initialize()` performs a TCP `M115` alongside the authenticated `/detail` call, but `verify_connection()` has decided `http_only` from the parsed model *before* touching TCP since the Creator 5 work — that family exposes no service on 8899, where an `M115` would hang until the connect timeout rather than fail fast. Model detection is PID-based end to end: the UDP discovery packet before pairing, `/detail` after. Rewritten as "Model Detection Without TCP", with the `http_only` guard stated as the rule and the two remaining ungated legacy call sites (`init_control`, `get_temperatures`, neither used by `ff-5mp-hass`) flagged. No code change — the guard and `tests/test_http_only_guard.py` were already correct; the document that exists to stop agents reintroducing TCP was the thing telling them to.

## [1.3.3] - 2026-07-26

### Changed

- **Diagnostic output now goes to the `logging` module instead of `print()`.** 95 `print()` calls across 10 modules were the library's only record of why an operation failed — and under Home Assistant, the largest consumer, stdout reaches nowhere the user can see. Every silent failure therefore looked identical from the outside: a `/detail` response the library could not parse, an unreachable printer, and a rejected check code all produced the same bare `None` or `False` with no explanation anywhere. That is the ambiguity behind both reports on `ff-5mp-hass#18`, where one reporter concluded their check code was wrong and another concluded the integration needed TCP port 8899; neither could see the actual cause. Failures and refused commands now log at `WARNING`, request/response tracing at `DEBUG`, under per-module loggers (`flashforge.api.controls.info`, `…job_control`, and so on) so consumers can raise the level for one area alone. Two intentional exceptions remain on stdout: `FlashForgePrinterDiscovery.print_debug_info()`, whose entire purpose is to dump a hex/ASCII view for a human, and the `_async_main` CLI demo.

### Security

- **Credentials, network identifiers, and cloud registration codes are redacted from logs.** Moving diagnostics into `logging` would otherwise have written secrets to a file users routinely paste into bug reports. The upload paths logged their full HTTP headers — including `serialNumber` and `checkCode`, which together are complete control of the printer over the LAN API — and `send_control_command` printed its whole payload, credentials included, on *every single command*. The new `flashforge.api.misc.redaction` helpers mask `serialNumber`, `checkCode`, `macAddr`, `ipAddr`, `flashRegisterCode`, and `polarRegisterCode` (in both firmware camelCase and library snake_case, recursing into nested structures) before any value can be formatted into a log record. The key set deliberately matches what `ff-5mp-hass` already strips from its diagnostics download, so a log paste and a diagnostics upload cannot disagree about what is safe to share.

## [1.3.2] - 2026-07-26

### Fixed

- **A firmware field this library has not seen no longer presents to the user as a wrong check code.** `Product`, `ProductResponse`, `ThumbnailResponse`, and `GenericResponse` — the envelope every inbound response inherits — were `extra="forbid"`, so one unrecognized key raised `ValidationError`. `send_product_command` caught it and returned a bare `False`, which is exactly what a printer refusing the credentials returns; `ff-5mp-hass` turns that into "the check code is incorrect". The same trap sat one level deeper on `/detail`: `FFPrinterDetail` has been `extra="allow"` since 1.3.0, but its children `MatlStationInfo`, `SlotInfo`, `IndepMatlInfo`, and `FFGcodeToolData` still forbade extras, and a child that rejects a field fails the whole response — most likely on a 4-head Creator 5 Pro reporting four loaded slots, the model least covered by existing fixtures. All inbound models now allow extras. Outbound request-parameter models (`AD5X*Params`, `Creator5*Params`, `FilamentArgs`) and the internally constructed `FFMachineInfo` / `Temperature` keep `extra="forbid"`, where it catches our own typos rather than a firmware revision. `send_product_command` now logs the `ValidationError` distinctly instead of letting an unparsed response impersonate rejected credentials. Reported as `ff-5mp-hass#18`.

- **`FFMachineInfo.has_matl_station` no longer misses the Material Station on the Creator 5 series.** It was a straight copy of the raw `hasMatlStation` value from `/detail`, which is an AD5X-only field — a Creator 5 Pro omits it entirely (verified on real hardware, pid 41, firmware 1.9.4) while reporting a fully populated `matlStationInfo` with four loaded slots. It therefore parsed as `None`, and consumers gating on it saw no station on exactly the models that have one. The parser already computed the correct value for its own AD5X heuristic (flag `is True` OR `slot_cnt > 0` OR non-empty `slot_infos`) and then discarded it; that derived value is now what the property exposes. Its type narrows from `bool | None` to `bool` — a capability has no "unknown" state, and offering one is what allowed an unreported flag to read as absent hardware. `FFPrinterDetail.has_matl_station` still carries the untouched firmware value.

- **`/gcodeList` no longer loses every file's metadata when the firmware adds a field.** `GCodeListResponse` and `FFGcodeFileEntry` were `extra="forbid"`, and `Files.get_recent_file_list()` caught the resulting `ValidationError` and fell back to a names-only list — `printing_time=0` and every other field `None`, for every file. One unrecognized key anywhere in the payload was therefore enough to silently strip print time, filament weight, and the per-tool material data on all models, and the result is byte-for-byte what a printer that genuinely reports names only looks like. Both models now use `extra="allow"` (matching `FFPrinterDetail`), and the remaining fallback logs a warning naming what was lost instead of degrading in silence.

## [1.3.1] - 2026-06-28

### Fixed

- **README "Supported Printers" table now lists the Creator 5 and Creator 5 Pro** that shipped in 1.3.0 (the table predated the Creator 5 work and omitted them). The Capabilities section now also reflects per-nozzle and chamber temperature control and the shared AD5X / Creator 5 material-station surface.

## [1.3.0] - 2026-06-28

### Added

- **Creator 5 / Creator 5 Pro support.** The library now detects and fully drives the Creator 5 and Creator 5 Pro (firmware PIDs `40` / `41`) over HTTP, bringing the Python port to parity with `ff-5mp-api-ts` v1.6.1 for these models. The port previously detected these printers via USB product ID during discovery but could not control them.
- **HTTP-only mode** for printers without a legacy TCP/8899 service (Creator 5 family). `FlashForgeClient` now exposes `is_creator5`, `is_creator5_pro`, and `http_only`; on an HTTP-only printer it skips the TCP bootstrap handshake and guards TCP-delegating control/temperature methods (`can_use_tcp`) so they no-op cleanly instead of hanging on a dead socket.
- **Structured Creator 5 machine info.** `FFMachineInfo` now surfaces `model`, `tool_temps` (per-nozzle), `nozzle_count`, `chamber`, and capability flags `has_camera`, `has_lidar`, and `has_door_sensor`; raw `/detail` fields `nozzle_temps`, `nozzle_target_temps`, and `lidar` are parsed on `FFPrinterDetail`.
- **HTTP temperature control transport** (`temperatureCtl_cmd`) for modern printers: `set_tool_temp`, `set_tool_temps`, `cancel_tool_temp` (per-nozzle, via the `nozzles[]` array), and `set_chamber_temp` / `cancel_chamber_temp` (Creator 5 only).
- **`creator5_palette`** — 24-entry Creator 5 color palette with CIEDE2000 nearest-color snapping (`snap_to_creator5_palette`). The color math was fuzz-verified against the TypeScript reference build across 4000 random RGB inputs with zero mismatches.
- **`configure_slot`** (`msConfig_cmd`) for material-station slot configuration, with model-gated color formatting: the Creator 5 snaps the color to its palette (sending `#RRGGBB` with the `#`), while the AD5X sends freeform `#`-stripped hex as before.
- **Creator 5 print-start and upload flows:** `start_creator5_job` (`/printGcode`) and `upload_file_creator5` (`/uploadGcode`) with the C5-native request shapes (no `firstLayerInspection`; booleans as the strings `"true"`/`"false"`; materials mapped at print-start rather than upload). New `Creator5JobParams` and `Creator5UploadParams` models.

### Fixed

- **`_is_new_firmware_version` no longer misreads the Creator 5 (and AD5X) as "old firmware".** These models always use the new payload/header format and their firmware versioning (e.g. the C5 reports `1.9.2`) isn't comparable to the 5M family's `3.x` line, so the numeric `3.1.3` threshold now short-circuits to the new format for them. Previously a Creator 5 would send a malformed legacy `/printGcode` body.
- **`get_file_list` / `get_local_file_list` no longer hang on HTTP-only printers.** They now fall back to the HTTP `/gcodeList` recent-file list (mirroring `Files.ts`) instead of blocking for ~10s on the dead TCP/8899 socket.
- **Creator 5 Pro is no longer mis-classified as a 5M Pro** by the legacy `"Pro" in name` heuristic when no firmware `pid` is present; the Creator 5 family is now checked first.

### Changed

- `AD5XMaterialMapping` is reused as the shared material-mapping type for both the AD5X and Creator 5 flows (both use the same 5-field wire shape). The two per-model validators now delegate to a single shared `_validate_mappings` helper.
- `set_chamber_temp` / `cancel_chamber_temp` are gated to Creator 5 / Creator 5 Pro (they return `False` on other models). This is a deliberate, documented divergence from the TypeScript client, which sends the chamber command unconditionally; see `docs/parity.md`.
## [1.2.3] - 2026-05-08

### Fixed

- Printer model detection (`is_pro`, `is_ad5x` on `FFMachineInfo`) now reads the firmware-set integer `pid` field on `/detail` instead of string-matching the user-mutable `name` field. Renaming an Adventurer 5M / 5M Pro / AD5X via the LCD or cloud no longer breaks model detection in downstream consumers (Home Assistant, Electron UI, Web UI). Falls back to the legacy name+capability heuristic when `pid` is absent so older firmware still works. Reported in [ff-5mp-hass#13](https://github.com/GhostTypes/ff-5mp-hass/issues/13).

### Added

- `FFMachineInfo.pid: int | None` — the raw firmware PID exposed for consumers that want to do their own model-class gating. Known modern HTTP-capable PIDs: `35` (Adventurer 5M), `36` (5M Pro), `38` (AD5X).

## [1.2.2] - 2026-04-27

### Fixed

- Replaced `netifaces` (source-only on PyPI) with `ifaddr` (pure-Python, wheels everywhere) for network interface enumeration. Fixes installation failure on Python 3.14 / Home Assistant 2026.4.x where `netifaces==0.11.0` cannot build, which previously caused `from flashforge import ...` to raise `ImportError` at module load and broke the Home Assistant config flow with "Invalid handler specified" — even for manual setup paths that didn't use discovery. Reported in [ff-5mp-hass#10](https://github.com/GhostTypes/ff-5mp-hass/issues/10).
- Synced `flashforge.__version__` with `pyproject.toml` (was stuck at `1.1.1`).

### Changed

- Added Python 3.14 to the supported versions classifier list.

## [1.2.1] - 2026-03-23

### Fixed

- Increased `currentPrintSpeed` and `printSpeedAdjust` validation limit from 200 to 1000 to support AD5X printers reporting speeds up to 500 (contributed by @spawnegit)
- Replaced per-request `aiohttp.ClientSession()` creation with shared HTTP session across all control modules (`control.py`, `files.py`, `info.py`, `job_control.py`), fixing connection churn and respecting the configured timeout
- Increased default HTTP timeout from 5s to 15s to prevent timeouts during print operations

### Changed

- Extracted duplicate `try/except aiohttp.ContentTypeError` JSON parsing pattern into a shared `json_from_response()` helper in `api/network/utils.py`
- Release workflow now includes curated changelog entry alongside auto-generated commit notes in GitHub Releases

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

[Unreleased]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.3.3...HEAD
[1.3.3]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.3.2...v1.3.3
[1.3.2]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.2.3...v1.3.0
[1.2.3]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/GhostTypes/ff-5mp-api-py/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.1.1
[1.0.2]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.2
[1.0.1]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.1
[1.0.0]: https://github.com/GhostTypes/ff-5mp-api-py/releases/tag/v1.0.0
