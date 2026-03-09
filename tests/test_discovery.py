"""Tests for universal and backward-compatible discovery behavior."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from flashforge.discovery import (
    DiscoveredPrinter,
    DiscoveryOptions,
    DiscoveryProtocol,
    FlashForgePrinter,
    FlashForgePrinterDiscovery,
    PrinterDiscovery,
    PrinterModel,
    PrinterStatus,
)


def _build_modern_buffer(
    *,
    name: str = "Adventurer 5M",
    command_port: int = 8899,
    vendor_id: int = 0x0403,
    product_id: int = 0x6001,
    product_type: int = 0x5A02,
    event_port: int = 8898,
    status_code: int = 0,
    serial_number: str = "SN123456",
) -> bytes:
    buffer = bytearray(276)
    buffer[0 : len(name)] = name.encode("utf-8")
    buffer[0x84:0x86] = command_port.to_bytes(2, byteorder="big")
    buffer[0x86:0x88] = vendor_id.to_bytes(2, byteorder="big")
    buffer[0x88:0x8A] = product_id.to_bytes(2, byteorder="big")
    buffer[0x8C:0x8E] = product_type.to_bytes(2, byteorder="big")
    buffer[0x8E:0x90] = event_port.to_bytes(2, byteorder="big")
    buffer[0x90:0x92] = status_code.to_bytes(2, byteorder="big")
    buffer[0x92 : 0x92 + len(serial_number)] = serial_number.encode("utf-8")
    return bytes(buffer)


def _build_legacy_buffer(
    *,
    name: str = "Adventurer 4",
    command_port: int = 8899,
    vendor_id: int = 0x0403,
    product_id: int = 0x001E,
    status_code: int = 0,
) -> bytes:
    buffer = bytearray(140)
    buffer[0 : len(name)] = name.encode("utf-8")
    buffer[0x84:0x86] = command_port.to_bytes(2, byteorder="big")
    buffer[0x86:0x88] = vendor_id.to_bytes(2, byteorder="big")
    buffer[0x88:0x8A] = product_id.to_bytes(2, byteorder="big")
    buffer[0x8A:0x8C] = status_code.to_bytes(2, byteorder="big")
    return bytes(buffer)


def test_flashforge_printer_string_representation():
    """Legacy wrapper printers still expose the historical string representation."""
    printer = FlashForgePrinter(
        name="Test Printer",
        serial_number="TEST123",
        ip_address="192.168.1.50",
    )

    assert str(printer) == "Name: Test Printer, Serial: TEST123, IP: 192.168.1.50"
    assert "FlashForgePrinter" in repr(printer)


def test_flashforge_printer_discovery_legacy_message_is_stable():
    """The legacy discovery wrapper keeps its historical UDP message surface."""
    discovery = FlashForgePrinterDiscovery()

    assert discovery.discovery_port == 48899
    assert discovery.listen_port == 18007
    assert len(discovery.discovery_message) == 20
    assert discovery.discovery_message[:7] == b"www.usr"


def test_legacy_wrapper_parses_historical_responses():
    """The wrapper still understands older fixed-offset payloads used by the Python API."""
    discovery = FlashForgePrinterDiscovery()
    response = bytearray(200)
    response[0:18] = b"Adventurer 5M Pro"
    response[0x92 : 0x92 + 11] = b"FF123456789"

    printer = discovery._parse_printer_response(bytes(response), "192.168.1.100")

    assert printer is not None
    assert printer.name == "Adventurer 5M Pro"
    assert printer.serial_number == "FF123456789"
    assert printer.ip_address == "192.168.1.100"


def test_legacy_wrapper_rejects_empty_or_invalid_responses():
    """Empty historical payloads should not produce fake printers."""
    discovery = FlashForgePrinterDiscovery()

    assert discovery._parse_printer_response(None, "192.168.1.100") is None
    assert discovery._parse_printer_response(b"short", "192.168.1.100") is None
    assert discovery._parse_printer_response(bytes(200), "192.168.1.100") is None


def test_calculate_broadcast_address():
    """Broadcast address calculation supports common subnets."""
    discovery = FlashForgePrinterDiscovery()

    assert discovery._calculate_broadcast_address("192.168.1.10", "255.255.255.0") == "192.168.1.255"
    assert discovery._calculate_broadcast_address("10.0.0.50", "255.255.0.0") == "10.0.255.255"
    assert discovery._calculate_broadcast_address("invalid", "255.255.255.0") is None


@patch("netifaces.interfaces")
@patch("netifaces.ifaddresses")
def test_get_broadcast_addresses(mock_ifaddresses, mock_interfaces):
    """Broadcast discovery still enumerates live interfaces with a global fallback."""
    discovery = FlashForgePrinterDiscovery()

    import netifaces

    mock_interfaces.return_value = ["eth0", "lo"]
    mock_ifaddresses.side_effect = lambda iface: {
        netifaces.AF_INET: [
            {
                "addr": "192.168.1.100" if iface == "eth0" else "127.0.0.1",
                "netmask": "255.255.255.0" if iface == "eth0" else "255.0.0.0",
            }
        ]
    }

    addresses = discovery._get_broadcast_addresses()

    assert "192.168.1.255" in addresses
    assert "255.255.255.255" in addresses
    assert "127.255.255.255" not in addresses


def test_parse_modern_protocol_parses_ad5x():
    """Modern 276-byte payloads should parse full AD5X metadata."""
    discovery = PrinterDiscovery()
    result = discovery.parse_modern_protocol(
        _build_modern_buffer(name="AD5X", product_type=0x5A02, serial_number="AD5X123456"),
        "192.168.1.100",
    )

    assert result.model == PrinterModel.AD5X
    assert result.protocol_format == DiscoveryProtocol.MODERN
    assert result.name == "AD5X"
    assert result.serial_number == "AD5X123456"
    assert result.command_port == 8899
    assert result.event_port == 8898


def test_parse_modern_protocol_parses_5m_pro():
    """Modern 5M Pro payloads should preserve product and status metadata."""
    discovery = PrinterDiscovery()
    result = discovery.parse_modern_protocol(
        _build_modern_buffer(
            name="Adventurer 5M Pro",
            product_type=0x5A02,
            status_code=1,
        ),
        "192.168.1.101",
    )

    assert result.model == PrinterModel.ADVENTURER_5M_PRO
    assert result.product_type == 0x5A02
    assert result.status == PrinterStatus.BUSY


def test_parse_legacy_protocol_parses_adventurer_4():
    """Legacy 140-byte payloads should detect Adventurer 4 correctly."""
    discovery = PrinterDiscovery()
    result = discovery.parse_legacy_protocol(
        _build_legacy_buffer(name="Adventurer 4"),
        "192.168.1.200",
    )

    assert result.model == PrinterModel.ADVENTURER_4
    assert result.protocol_format == DiscoveryProtocol.LEGACY
    assert result.name == "Adventurer 4"
    assert result.serial_number is None
    assert result.event_port is None


def test_detect_legacy_model_uses_product_id_fallback():
    """Legacy PID fallback covers renamed Adventurer 3 and Adventurer 4 printers."""
    discovery = PrinterDiscovery()

    assert discovery.detect_legacy_model("Workshop Printer", 0x001E) == PrinterModel.ADVENTURER_4
    assert discovery.detect_legacy_model("Workshop Printer", 0x0008) == PrinterModel.ADVENTURER_3


def test_map_status_code():
    """Discovery status codes map to the typed enum surface."""
    discovery = PrinterDiscovery()

    assert discovery.map_status_code(0) == PrinterStatus.READY
    assert discovery.map_status_code(1) == PrinterStatus.BUSY
    assert discovery.map_status_code(2) == PrinterStatus.ERROR
    assert discovery.map_status_code(999) == PrinterStatus.UNKNOWN


def test_parse_discovery_response_invalid_size_returns_none():
    """Undersized UDP payloads should be ignored rather than raising."""
    discovery = PrinterDiscovery()

    assert discovery.parse_discovery_response(b"short", "192.168.1.100") is None


@pytest.mark.asyncio
async def test_discover_prefers_modern_duplicates():
    """When duplicate responses exist, the modern protocol wins for the same printer."""
    discovery = PrinterDiscovery()
    fake_transport = Mock()
    fake_transport.close = Mock()

    legacy = DiscoveredPrinter(
        model=PrinterModel.ADVENTURER_5M,
        protocol_format=DiscoveryProtocol.LEGACY,
        name="Adventurer 5M",
        ip_address="192.168.1.100",
        command_port=8899,
    )
    modern = DiscoveredPrinter(
        model=PrinterModel.ADVENTURER_5M_PRO,
        protocol_format=DiscoveryProtocol.MODERN,
        name="Adventurer 5M Pro",
        ip_address="192.168.1.100",
        command_port=8899,
        serial_number="SN123456",
    )

    with (
        patch.object(discovery, "_create_endpoint", AsyncMock(return_value=(fake_transport, Mock()))),
        patch.object(discovery, "_send_discovery_packets"),
        patch.object(discovery, "_receive_responses", AsyncMock(return_value=[legacy, modern])),
    ):
        printers = await discovery.discover(DiscoveryOptions(timeout=50, idle_timeout=10, max_retries=1))

    assert printers == [modern]


@pytest.mark.asyncio
async def test_discovery_monitor_emits_discovered_and_end_events():
    """The monitor API should emit discovered and end events like the TS library."""
    discovery = PrinterDiscovery()
    fake_transport = Mock()
    fake_transport.close = Mock()

    async def fake_create_endpoint(message_queue, error_queue):
        async def feed_queue():
            await asyncio.sleep(0)
            message_queue.put_nowait(
                (
                    _build_modern_buffer(name="AD5X", serial_number="AD5X123456"),
                    ("192.168.1.120", 8899),
                )
            )

        asyncio.create_task(feed_queue())
        return fake_transport, Mock()

    with (
        patch.object(discovery, "_create_endpoint", side_effect=fake_create_endpoint),
        patch.object(discovery, "_send_discovery_packets"),
    ):
        discovered: list[DiscoveredPrinter] = []
        ended = asyncio.Event()
        monitor = discovery.monitor(DiscoveryOptions(timeout=50, idle_timeout=10, max_retries=1))
        monitor.on("discovered", discovered.append)
        monitor.on("end", lambda: ended.set())

        await asyncio.wait_for(ended.wait(), timeout=1)
        monitor.stop()

    assert len(discovered) == 1
    assert discovered[0].model == PrinterModel.AD5X
    assert discovered[0].serial_number == "AD5X123456"


@pytest.mark.asyncio
async def test_legacy_wrapper_discover_printers_async_returns_wrapper_objects():
    """The historical wrapper still converts universal discovery results into FlashForgePrinter."""
    discovery = FlashForgePrinterDiscovery()
    discovered_printer = DiscoveredPrinter(
        model=PrinterModel.ADVENTURER_4,
        protocol_format=DiscoveryProtocol.LEGACY,
        name="Adventurer 4",
        ip_address="192.168.1.210",
        command_port=8899,
        serial_number="ADV4SN",
    )

    with patch.object(
        discovery._discovery,
        "discover",
        AsyncMock(return_value=[discovered_printer]),
    ):
        printers = await discovery.discover_printers_async(timeout_ms=50, idle_timeout_ms=10, max_retries=1)

    assert printers == [
        FlashForgePrinter(
            name="Adventurer 4",
            serial_number="ADV4SN",
            ip_address="192.168.1.210",
        )
    ]
