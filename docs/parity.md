# Python and TypeScript Parity

The Python and TypeScript FlashForge APIs share a common protocol and model baseline, but they do not promise strict 1:1 public API parity.

## Shared Core

These concepts are expected to exist in both libraries:

- modern client for Adventurer 5M, 5M Pro, and AD5X
- discovery support for modern and legacy FlashForge models
- HTTP control, job, info, file, and temperature modules
- low-level TCP access
- AD5X-specific models and job flows
- machine-info and response-model coverage

## Python-Specific Surface

The Python library intentionally includes extra Python-oriented helpers:

- `FlashForgeClient` as the main modern client
- snake_case method names
- async context-manager support
- convenience wrappers like `get_printer_status()`, `pause_print()`, and `home_all_axes()`
- compatibility discovery wrapper `FlashForgePrinterDiscovery`
- integration-oriented capability overrides such as `set_feature_overrides(...)`

## TypeScript-Specific Surface

The TypeScript library intentionally includes its own TypeScript-shaped surface:

- `FiveMClient` as the main modern client
- camelCase method names
- `PrinterDiscovery` as the primary discovery entry point
- fewer high-level convenience wrappers on the top-level client

## Guidance

- Prefer `PrinterDiscovery` for new code in both languages.
- Treat `FlashForgePrinterDiscovery` as a Python compatibility wrapper, not the preferred modern API.
- Do not assume a convenience helper exists in both languages just because the underlying capability exists in both.

## Recommended Public Entry Points

| Use Case | Python | TypeScript |
| --- | --- | --- |
| Modern printer client | `FlashForgeClient` | `FiveMClient` |
| Modern discovery API | `PrinterDiscovery` | `PrinterDiscovery` |
| Compatibility discovery API | `FlashForgePrinterDiscovery` | n/a |
| Legacy TCP / low-level access | TCP client modules | `FlashForgeClient` / `FlashForgeTcpClient` |
