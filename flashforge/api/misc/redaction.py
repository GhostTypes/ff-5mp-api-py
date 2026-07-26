"""
FlashForge Python API - Log redaction helpers.

Debug logs get pasted into bug reports verbatim, so anything that identifies or
grants control of a printer is masked before it can be formatted into a log
record. The key set mirrors what ``ff-5mp-hass`` already strips from its
diagnostics download, so the two surfaces cannot disagree about what is safe to
share.

- ``serialNumber`` / ``checkCode``: together these are full control of the
  printer over the LAN API.
- ``flashRegisterCode`` / ``polarRegisterCode``: cloud-account registration
  codes.
- ``macAddr`` / ``ipAddr``: identify the machine and its network.
"""

from typing import Any

REDACTED = "<redacted>"

# Both the firmware's camelCase aliases and the library's snake_case field
# names, since payloads are logged in either form depending on the call site.
SENSITIVE_KEYS = frozenset(
    {
        "serialNumber",
        "serial_number",
        "checkCode",
        "check_code",
        "macAddr",
        "mac_addr",
        "mac_address",
        "ipAddr",
        "ip_addr",
        "ip_address",
        "flashRegisterCode",
        "flash_register_code",
        "flash_cloud_register_code",
        "polarRegisterCode",
        "polar_register_code",
        "polar_cloud_register_code",
    }
)


def _redact_value(value: Any) -> Any:
    """Recurse into nested containers so a sensitive key cannot hide one level down."""
    if isinstance(value, dict):
        return redact_mapping(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def redact_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``mapping`` with every sensitive value masked.

    The input is never mutated - callers are usually about to send it.
    """
    return {
        key: (REDACTED if key in SENSITIVE_KEYS else _redact_value(value))
        for key, value in mapping.items()
    }


def redact_model(model: Any) -> Any:
    """Return a log-safe representation of a Pydantic model (or anything else).

    Falls back to ``repr`` for objects that cannot be dumped, and to a plain
    ``<unloggable>`` if even that raises - a redaction helper must never be the
    reason an error path fails.
    """
    if model is None:
        return None

    dump = getattr(model, "model_dump", None)
    if callable(dump):
        try:
            return redact_mapping(dump())
        except Exception:  # noqa: BLE001 - logging must not raise
            pass

    if isinstance(model, dict):
        return redact_mapping(model)

    try:
        return repr(model)
    except Exception:  # noqa: BLE001
        return "<unloggable>"
