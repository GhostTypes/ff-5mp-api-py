"""
Tests for the library's diagnostic logging.

Every failure path here used to `print()`. Under Home Assistant - the largest
consumer - stdout goes nowhere the user can reach, so a printer that failed to
parse looked identical to a printer that rejected the check code, and neither
reporter on ff-5mp-hass#18 could produce evidence of which one they had. These
tests pin the two properties that make that debuggable: the failure reaches the
log, and the credentials do not.
"""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flashforge.api.misc.redaction import redact_mapping, redact_model
from flashforge.client import FlashForgeClient

INFO_LOGGER = "flashforge.api.controls.info"
CONTROL_LOGGER = "flashforge.api.controls.control"


def _mock_session(response_payload: dict, status: int = 200):
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=response_payload)
    mock_response.text = AsyncMock(return_value=json.dumps(response_payload))

    mock_post_ctx = MagicMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=mock_post_ctx)
    return mock_session


def _build_client() -> FlashForgeClient:
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.tcp_client = AsyncMock()
    return client


def test_redact_masks_the_serial_number_and_check_code():
    """Upload headers carry full control of the printer; logs must not."""
    headers = {
        "serialNumber": "SN123456789",
        "checkCode": "abcd1234",
        "fileSize": "4096",
        "printNow": "true",
    }

    redacted = redact_mapping(headers)

    assert redacted["serialNumber"] == "<redacted>"
    assert redacted["checkCode"] == "<redacted>"
    # Everything else survives, or the log line is useless.
    assert redacted["fileSize"] == "4096"
    assert redacted["printNow"] == "true"
    # The caller's dict is untouched - these headers are about to be sent.
    assert headers["serialNumber"] == "SN123456789"
    assert headers["checkCode"] == "abcd1234"


def test_redact_output_contains_no_sensitive_substring():
    """The formatted line is what lands in a bug report, so check that."""
    headers = {"serialNumber": "SN123456789", "checkCode": "abcd1234", "fileSize": "1"}

    formatted = str(redact_mapping(headers))

    assert "SN123456789" not in formatted
    assert "abcd1234" not in formatted


def test_redact_masks_the_network_and_cloud_identifiers():
    """Not just credentials: /detail also carries the MAC, IP and cloud codes.

    The key set matches what ff-5mp-hass strips from its diagnostics download,
    so a log paste and a diagnostics upload cannot disagree about what is safe.
    """
    detail = {
        "macAddr": "AA:BB:CC:DD:EE:FF",
        "ipAddr": "192.168.1.120",
        "flashRegisterCode": "FRC-9999",
        "polarRegisterCode": "PRC-8888",
        "firmwareVersion": "1.9.4",
    }

    redacted = redact_mapping(detail)

    assert redacted["macAddr"] == "<redacted>"
    assert redacted["ipAddr"] == "<redacted>"
    assert redacted["flashRegisterCode"] == "<redacted>"
    assert redacted["polarRegisterCode"] == "<redacted>"
    # Diagnostic values that identify nothing must survive.
    assert redacted["firmwareVersion"] == "1.9.4"


def test_redact_masks_snake_case_field_names_too():
    """Payloads are logged as firmware aliases or as library field names."""
    redacted = redact_mapping(
        {"mac_address": "AA:BB:CC:DD:EE:FF", "ip_address": "10.0.0.5", "check_code": "abcd"}
    )

    assert redacted["mac_address"] == "<redacted>"
    assert redacted["ip_address"] == "<redacted>"
    assert redacted["check_code"] == "<redacted>"


def test_redact_recurses_into_nested_containers():
    """A sensitive key one level down is still a leak."""
    formatted = str(
        redact_mapping(
            {
                "payload": {"macAddr": "AA:BB:CC:DD:EE:FF"},
                "printers": [{"ipAddr": "192.168.1.120"}],
            }
        )
    )

    assert "AA:BB:CC:DD:EE:FF" not in formatted
    assert "192.168.1.120" not in formatted


def test_redact_model_masks_a_pydantic_detail_payload():
    """The /detail debug dump goes through a model, not a dict."""
    from flashforge.models.machine_info import FFPrinterDetail

    detail = FFPrinterDetail(
        macAddr="AA:BB:CC:DD:EE:FF",
        ipAddr="192.168.1.120",
        flashRegisterCode="FRC-9999",
        firmwareVersion="1.9.4",
    )

    formatted = str(redact_model(detail))

    assert "AA:BB:CC:DD:EE:FF" not in formatted
    assert "192.168.1.120" not in formatted
    assert "FRC-9999" not in formatted
    assert "1.9.4" in formatted


def test_redact_model_never_raises_on_an_odd_object():
    """A redaction helper must not be why an error path fails."""

    class Awkward:
        def model_dump(self):
            raise RuntimeError("nope")

        def __repr__(self):
            return "Awkward()"

    assert redact_model(Awkward()) == "Awkward()"
    assert redact_model(None) is None


@pytest.mark.asyncio
async def test_detail_parse_failure_is_logged(caplog):
    """A /detail that will not parse must say so.

    `get_detail_response` returns None for every failure, and ff-5mp-hass turns
    that into "Failed to connect ... check the IP address and credentials". The
    log line is the only thing that distinguishes a parse failure from a real
    connection problem or a wrong check code.
    """
    client = _build_client()
    # `code` is required by GenericResponse, so this fails validation regardless
    # of how permissive the models are about extra fields.
    mock_session = _mock_session({"detail": {}})

    with caplog.at_level(logging.WARNING, logger=INFO_LOGGER):
        with patch.object(client, "get_http_session", AsyncMock(return_value=mock_session)):
            result = await client.info.get_detail_response()

    assert result is None
    assert "Could not read /detail" in caplog.text


@pytest.mark.asyncio
async def test_detail_non_200_is_logged(caplog):
    """The other silent path out of the same method."""
    client = _build_client()
    mock_session = _mock_session({}, status=500)

    with caplog.at_level(logging.WARNING, logger=INFO_LOGGER):
        with patch.object(client, "get_http_session", AsyncMock(return_value=mock_session)):
            result = await client.info.get_detail_response()

    assert result is None
    assert "Non-200 status" in caplog.text
    assert "500" in caplog.text


@pytest.mark.asyncio
async def test_control_command_debug_log_omits_the_credentials(caplog):
    """The control payload embeds the serial number and check code.

    It used to be printed whole on every single command.
    """
    client = _build_client()
    client.led_control = True
    mock_session = _mock_session({"code": 0, "message": "Success"})

    with caplog.at_level(logging.DEBUG, logger=CONTROL_LOGGER):
        with patch.object(client, "get_http_session", AsyncMock(return_value=mock_session)):
            with patch.object(client, "is_http_client_busy", AsyncMock(return_value=False)):
                await client.control.set_led_on()

    assert "Sending control command" in caplog.text
    assert "SN123" not in caplog.text
    assert "CODE123" not in caplog.text


def test_capability_refusals_are_logged_not_printed(caplog):
    """A refused command returns a bare False; the reason belongs in the log."""
    client = _build_client()
    client.led_control = False

    with caplog.at_level(logging.WARNING, logger=CONTROL_LOGGER):
        import asyncio

        assert asyncio.run(client.control.set_led_on()) is False

    assert "LED control is not equipped" in caplog.text
