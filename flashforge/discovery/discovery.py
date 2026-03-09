"""
Universal FlashForge printer discovery using UDP broadcast and multicast.
"""

from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Any

import netifaces

logger = logging.getLogger(__name__)

MULTICAST_ADDRESS = "225.0.0.9"
MODERN_PROTOCOL_SIZE = 276
LEGACY_PROTOCOL_SIZE = 140

LEGACY_PRODUCT_IDS = {
    "Adventurer3": 0x0008,
    "Adventurer4": 0x001E,
}


class DiscoveryError(Exception):
    """Base error for discovery-related failures."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


class InvalidResponseError(DiscoveryError):
    """Raised when a discovery response has an unexpected size."""

    def __init__(self, size: int, address: str) -> None:
        super().__init__(f"Invalid response size: {size} bytes from {address}", "INVALID_RESPONSE")
        self.response_size = size
        self.address = address


class SocketCreationError(DiscoveryError):
    """Raised when a UDP discovery socket cannot be created."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "SOCKET_CREATION_FAILED")


class DiscoveryTimeoutError(DiscoveryError):
    """Raised when discovery times out without any responses."""

    def __init__(self, timeout_ms: int) -> None:
        super().__init__(f"Discovery timeout after {timeout_ms}ms", "DISCOVERY_TIMEOUT")
        self.timeout_ms = timeout_ms


class PrinterModel(StrEnum):
    """Known FlashForge printer models discoverable on LAN."""

    AD5X = "AD5X"
    ADVENTURER_5M = "Adventurer5M"
    ADVENTURER_5M_PRO = "Adventurer5MPro"
    ADVENTURER_4 = "Adventurer4"
    ADVENTURER_3 = "Adventurer3"
    UNKNOWN = "Unknown"


class DiscoveryProtocol(StrEnum):
    """Discovery response wire formats."""

    MODERN = "modern"
    LEGACY = "legacy"


class PrinterStatus(IntEnum):
    """Printer status reported via UDP discovery."""

    READY = 0
    BUSY = 1
    ERROR = 2
    UNKNOWN = 3


@dataclass(slots=True)
class DiscoveredPrinter:
    """Typed printer metadata returned by universal discovery."""

    model: PrinterModel
    protocol_format: DiscoveryProtocol
    name: str
    ip_address: str
    command_port: int
    serial_number: str | None = None
    event_port: int | None = None
    vendor_id: int | None = None
    product_id: int | None = None
    product_type: int | None = None
    status_code: int | None = None
    status: PrinterStatus | None = None


@dataclass(slots=True)
class DiscoveryOptions:
    """Configuration options for printer discovery."""

    timeout: int = 10000
    idle_timeout: int = 1500
    max_retries: int = 3
    use_multicast: bool = True
    use_broadcast: bool = True
    ports: list[int] = field(default_factory=lambda: [8899, 19000, 48899])


@dataclass(slots=True)
class FlashForgePrinter:
    """
    Backward-compatible legacy discovery result.

    This keeps the historical Python surface used by ff-5mp-hass while the richer
    DiscoveredPrinter metadata is exposed via PrinterDiscovery.
    """

    name: str = ""
    serial_number: str = ""
    ip_address: str = ""

    @classmethod
    def from_discovered_printer(cls, printer: DiscoveredPrinter) -> FlashForgePrinter:
        return cls(
            name=printer.name,
            serial_number=printer.serial_number or "",
            ip_address=printer.ip_address,
        )

    def __str__(self) -> str:
        return f"Name: {self.name}, Serial: {self.serial_number}, IP: {self.ip_address}"

    def __repr__(self) -> str:
        return (
            "FlashForgePrinter("
            f"name='{self.name}', serial_number='{self.serial_number}', ip_address='{self.ip_address}')"
        )


class _DiscoveryDatagramProtocol(asyncio.DatagramProtocol):
    """Asyncio protocol used to push UDP datagrams into an async queue."""

    def __init__(
        self,
        message_queue: asyncio.Queue[tuple[bytes, tuple[str, int]]],
        error_queue: asyncio.Queue[Exception],
    ) -> None:
        self.message_queue = message_queue
        self.error_queue = error_queue

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.message_queue.put_nowait((data, addr))

    def error_received(self, exc: Exception) -> None:
        self.error_queue.put_nowait(exc)


class DiscoveryMonitor:
    """Event-based continuous discovery monitor."""

    def __init__(self, discovery: PrinterDiscovery, options: DiscoveryOptions) -> None:
        self._discovery = discovery
        self._options = options
        self._listeners: dict[str, list[Callable[..., Any]]] = {
            "discovered": [],
            "end": [],
            "error": [],
        }
        self._transport: asyncio.DatagramTransport | None = None
        self._task = asyncio.create_task(self._run())
        self._stopped = False
        self._end_emitted = False

    def on(self, event: str, callback: Callable[..., Any]) -> DiscoveryMonitor:
        """Register an event callback."""
        self._listeners.setdefault(event, []).append(callback)
        return self

    def stop(self) -> None:
        """Stop monitoring and clean up resources."""
        if self._stopped:
            return
        self._stopped = True
        if self._transport:
            self._transport.close()
            self._transport = None
        if not self._task.done():
            self._task.cancel()
        self._emit_end_if_needed()

    async def _run(self) -> None:
        discovered_keys: set[str] = set()
        message_queue: asyncio.Queue[tuple[bytes, tuple[str, int]]] = asyncio.Queue()
        error_queue: asyncio.Queue[Exception] = asyncio.Queue()
        last_response_at: float | None = None
        send_interval_seconds = self._options.timeout / 1000.0
        total_timeout_seconds = (self._options.timeout * self._options.max_retries) / 1000.0

        try:
            self._transport, _ = await self._discovery._create_endpoint(message_queue, error_queue)
            self._discovery._send_discovery_packets(self._transport, self._options)

            loop = asyncio.get_running_loop()
            started_at = loop.time()
            next_send_at = started_at + send_interval_seconds

            while not self._stopped:
                now = loop.time()
                if now - started_at >= total_timeout_seconds:
                    break

                if (
                    last_response_at is not None
                    and now - last_response_at >= self._options.idle_timeout / 1000.0
                ):
                    break

                if now >= next_send_at:
                    self._discovery._send_discovery_packets(self._transport, self._options)
                    next_send_at = now + send_interval_seconds

                wait_timeout = min(0.1, max(total_timeout_seconds - (now - started_at), 0.0))
                try:
                    data, addr = await asyncio.wait_for(message_queue.get(), timeout=wait_timeout)
                except TimeoutError:
                    if not error_queue.empty():
                        error = error_queue.get_nowait()
                        self._emit("error", error)
                    continue

                printer = self._discovery.parse_discovery_response(data, addr[0])
                if printer is None:
                    continue

                last_response_at = loop.time()
                key = f"{printer.ip_address}:{printer.command_port}"
                if key not in discovered_keys:
                    discovered_keys.add(key)
                    self._emit("discovered", printer)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self._emit("error", error)
        finally:
            if self._transport:
                self._transport.close()
                self._transport = None
            self._emit_end_if_needed()

    def _emit(self, event: str, *args: Any) -> None:
        listeners = list(self._listeners.get(event, []))
        if event == "error" and not listeners:
            logger.error("Discovery monitor error: %s", args[0] if args else "unknown error")
            return
        for callback in listeners:
            callback(*args)

    def _emit_end_if_needed(self) -> None:
        if self._end_emitted:
            return
        self._end_emitted = True
        for callback in list(self._listeners.get("end", [])):
            callback()


class PrinterDiscovery:
    """Universal FlashForge printer discovery using UDP broadcast and multicast."""

    async def discover(self, options: DiscoveryOptions | None = None) -> list[DiscoveredPrinter]:
        config = options or DiscoveryOptions()
        printers: dict[str, DiscoveredPrinter] = {}

        for attempt in range(config.max_retries):
            message_queue: asyncio.Queue[tuple[bytes, tuple[str, int]]] = asyncio.Queue()
            error_queue: asyncio.Queue[Exception] = asyncio.Queue()
            transport: asyncio.DatagramTransport | None = None
            try:
                transport, _ = await self._create_endpoint(message_queue, error_queue)
                self._send_discovery_packets(transport, config)
                discovered_printers = await self._receive_responses(message_queue, error_queue, config)

                for printer in discovered_printers:
                    key = f"{printer.ip_address}:{printer.command_port}"
                    existing = printers.get(key)
                    if existing is None or printer.protocol_format == DiscoveryProtocol.MODERN:
                        printers[key] = printer

                if printers:
                    break
            finally:
                if transport is not None:
                    transport.close()

            if attempt < config.max_retries - 1:
                await asyncio.sleep(1.0)

        return list(printers.values())

    def monitor(self, options: DiscoveryOptions | None = None) -> DiscoveryMonitor:
        """Create an event-based continuous discovery monitor."""
        return DiscoveryMonitor(self, options or DiscoveryOptions())

    async def _create_endpoint(
        self,
        message_queue: asyncio.Queue[tuple[bytes, tuple[str, int]]],
        error_queue: asyncio.Queue[Exception],
    ) -> tuple[asyncio.DatagramTransport, _DiscoveryDatagramProtocol]:
        loop = asyncio.get_running_loop()
        try:
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: _DiscoveryDatagramProtocol(message_queue, error_queue),
                local_addr=("0.0.0.0", 0),
                allow_broadcast=True,
            )
        except Exception as error:
            raise SocketCreationError(str(error)) from error
        return transport, protocol

    async def _receive_responses(
        self,
        message_queue: asyncio.Queue[tuple[bytes, tuple[str, int]]],
        error_queue: asyncio.Queue[Exception],
        options: DiscoveryOptions,
    ) -> list[DiscoveredPrinter]:
        printers: list[DiscoveredPrinter] = []
        loop = asyncio.get_running_loop()
        started_at = loop.time()
        last_response_at = started_at
        total_timeout_seconds = options.timeout / 1000.0
        idle_timeout_seconds = options.idle_timeout / 1000.0

        while True:
            now = loop.time()
            if now - started_at >= total_timeout_seconds:
                break
            if now - last_response_at >= idle_timeout_seconds:
                break

            try:
                data, addr = await asyncio.wait_for(message_queue.get(), timeout=0.1)
            except TimeoutError:
                if not error_queue.empty():
                    logger.error("Socket error during discovery: %s", error_queue.get_nowait())
                continue

            last_response_at = loop.time()
            printer = self.parse_discovery_response(data, addr[0])
            if printer is not None:
                printers.append(printer)

        return printers

    def _send_discovery_packets(
        self,
        transport: asyncio.DatagramTransport,
        options: DiscoveryOptions,
    ) -> None:
        packet = b""

        if options.use_multicast:
            self._join_multicast_group(transport)
            for port in options.ports:
                if port in {8899, 19000}:
                    try:
                        transport.sendto(packet, (MULTICAST_ADDRESS, port))
                    except Exception as error:
                        logger.warning(
                            "Discovery: Failed to send multicast to %s:%s - %s",
                            MULTICAST_ADDRESS,
                            port,
                            error,
                        )

        if options.use_broadcast:
            for address in self.get_broadcast_addresses():
                for port in options.ports:
                    if port == 48899:
                        try:
                            transport.sendto(packet, (address, port))
                        except Exception as error:
                            logger.warning(
                                "Discovery: Failed to send broadcast to %s:%s - %s",
                                address,
                                port,
                                error,
                            )

            for port in options.ports:
                try:
                    transport.sendto(packet, ("255.255.255.255", port))
                except Exception as error:
                    logger.warning(
                        "Discovery: Failed to send to broadcast 255.255.255.255:%s - %s",
                        port,
                        error,
                    )

    def parse_discovery_response(
        self,
        buffer: bytes,
        ip_address: str,
    ) -> DiscoveredPrinter | None:
        """Parse a UDP discovery response and return typed printer metadata."""
        if not buffer:
            return None

        try:
            if len(buffer) >= MODERN_PROTOCOL_SIZE:
                return self.parse_modern_protocol(buffer, ip_address)
            if len(buffer) >= LEGACY_PROTOCOL_SIZE:
                return self.parse_legacy_protocol(buffer, ip_address)

            logger.warning("Invalid discovery response: %s bytes from %s", len(buffer), ip_address)
            return None
        except Exception as error:
            logger.error("Error parsing discovery response: %s", error)
            return None

    def parse_modern_protocol(self, buffer: bytes, ip_address: str) -> DiscoveredPrinter:
        """Parse a modern 276-byte discovery response."""
        if len(buffer) < MODERN_PROTOCOL_SIZE:
            raise InvalidResponseError(len(buffer), ip_address)

        name = buffer[0:0x84].decode("utf-8", errors="ignore").split("\x00", 1)[0]
        command_port = int.from_bytes(buffer[0x84:0x86], byteorder="big")
        vendor_id = int.from_bytes(buffer[0x86:0x88], byteorder="big")
        product_id = int.from_bytes(buffer[0x88:0x8A], byteorder="big")
        product_type = int.from_bytes(buffer[0x8C:0x8E], byteorder="big")
        event_port = int.from_bytes(buffer[0x8E:0x90], byteorder="big")
        status_code = int.from_bytes(buffer[0x90:0x92], byteorder="big")
        serial_number = buffer[0x92 : 0x92 + 130].decode("utf-8", errors="ignore").split("\x00", 1)[0]
        model = self.detect_modern_model(name, product_type)

        return DiscoveredPrinter(
            model=model,
            protocol_format=DiscoveryProtocol.MODERN,
            name=name,
            ip_address=ip_address,
            command_port=command_port,
            serial_number=serial_number,
            event_port=event_port,
            vendor_id=vendor_id,
            product_id=product_id,
            product_type=product_type,
            status_code=status_code,
            status=self.map_status_code(status_code),
        )

    def parse_legacy_protocol(self, buffer: bytes, ip_address: str) -> DiscoveredPrinter:
        """Parse a legacy 140-byte discovery response."""
        if len(buffer) < LEGACY_PROTOCOL_SIZE:
            raise InvalidResponseError(len(buffer), ip_address)

        name = buffer[0:0x80].decode("utf-8", errors="ignore").split("\x00", 1)[0]
        command_port = int.from_bytes(buffer[0x84:0x86], byteorder="big")
        vendor_id = int.from_bytes(buffer[0x86:0x88], byteorder="big")
        product_id = int.from_bytes(buffer[0x88:0x8A], byteorder="big")
        status_code = int.from_bytes(buffer[0x8A:0x8C], byteorder="big")
        model = self.detect_legacy_model(name, product_id)

        return DiscoveredPrinter(
            model=model,
            protocol_format=DiscoveryProtocol.LEGACY,
            name=name,
            ip_address=ip_address,
            command_port=command_port,
            vendor_id=vendor_id,
            product_id=product_id,
            status_code=status_code,
            status=self.map_status_code(status_code),
        )

    def detect_modern_model(self, name: str, product_type: int) -> PrinterModel:
        """Detect a modern printer model from discovery metadata."""
        upper_name = name.upper()

        if upper_name == "AD5X":
            return PrinterModel.AD5X

        if product_type == 0x5A02:
            if "PRO" in upper_name:
                return PrinterModel.ADVENTURER_5M_PRO
            return PrinterModel.ADVENTURER_5M

        if "ADVENTURER 5M" in upper_name or "AD5M" in upper_name:
            if "PRO" in upper_name:
                return PrinterModel.ADVENTURER_5M_PRO
            return PrinterModel.ADVENTURER_5M

        return PrinterModel.UNKNOWN

    def detect_legacy_model(self, name: str, product_id: int | None = None) -> PrinterModel:
        """Detect a legacy printer model from discovery metadata."""
        upper_name = name.upper()

        if "ADVENTURER 4" in upper_name or "ADVENTURER4" in upper_name or "AD4" in upper_name:
            return PrinterModel.ADVENTURER_4

        if "ADVENTURER 3" in upper_name or "ADVENTURER3" in upper_name or "AD3" in upper_name:
            return PrinterModel.ADVENTURER_3

        if product_id == LEGACY_PRODUCT_IDS["Adventurer4"]:
            return PrinterModel.ADVENTURER_4

        if product_id == LEGACY_PRODUCT_IDS["Adventurer3"]:
            return PrinterModel.ADVENTURER_3

        return PrinterModel.UNKNOWN

    def map_status_code(self, status_code: int) -> PrinterStatus:
        """Map discovery status codes to the typed printer status enum."""
        if status_code == 0:
            return PrinterStatus.READY
        if status_code == 1:
            return PrinterStatus.BUSY
        if status_code == 2:
            return PrinterStatus.ERROR
        return PrinterStatus.UNKNOWN

    def get_broadcast_addresses(self) -> list[str]:
        """Retrieve broadcast addresses for all active IPv4 interfaces."""
        broadcast_addresses: list[str] = []

        try:
            for interface_name in netifaces.interfaces():
                try:
                    addresses = netifaces.ifaddresses(interface_name)
                    if netifaces.AF_INET not in addresses:
                        continue

                    for addr_info in addresses[netifaces.AF_INET]:
                        if addr_info.get("addr", "").startswith("127."):
                            continue

                        ip_addr = addr_info.get("addr")
                        netmask = addr_info.get("netmask")
                        if not ip_addr or not netmask:
                            continue

                        broadcast = self.calculate_broadcast_address(ip_addr, netmask)
                        if broadcast and broadcast not in broadcast_addresses:
                            broadcast_addresses.append(broadcast)
                except Exception as error:
                    logger.warning("Error processing interface %s: %s", interface_name, error)
        except Exception as error:
            logger.error("Error getting network interfaces: %s", error)
            broadcast_addresses = ["255.255.255.255", "192.168.1.255", "192.168.0.255"]

        if "255.255.255.255" not in broadcast_addresses:
            broadcast_addresses.append("255.255.255.255")

        return broadcast_addresses

    def calculate_broadcast_address(self, ip_address: str, subnet_mask: str) -> str | None:
        """Calculate an IPv4 broadcast address from IP and subnet mask."""
        try:
            ip_parts = [int(part) for part in ip_address.split(".")]
            mask_parts = [int(part) for part in subnet_mask.split(".")]
            if len(ip_parts) != 4 or len(mask_parts) != 4:
                return None
            broadcast_parts = [ip_parts[index] | (~mask_parts[index] & 255) for index in range(4)]
            return ".".join(str(part) for part in broadcast_parts)
        except Exception:
            return None

    def _join_multicast_group(self, transport: asyncio.DatagramTransport) -> None:
        """Join the discovery multicast group if the OS/network stack allows it."""
        get_extra_info = getattr(transport, "get_extra_info", None)
        if get_extra_info is None:
            return

        raw_socket = get_extra_info("socket")
        if raw_socket is None:
            return

        try:
            membership = socket.inet_aton(MULTICAST_ADDRESS) + socket.inet_aton("0.0.0.0")
            raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        except Exception as error:
            logger.warning(
                "Discovery: Failed to join multicast group %s - %s",
                MULTICAST_ADDRESS,
                error,
            )


class FlashForgePrinterDiscovery:
    """Backward-compatible wrapper around the universal PrinterDiscovery API."""

    DISCOVERY_PORT = 48899
    LISTEN_PORT = 18007

    def __init__(self) -> None:
        self.discovery_port = self.DISCOVERY_PORT
        self.listen_port = self.LISTEN_PORT
        self.discovery_message = bytes(
            [
                0x77,
                0x77,
                0x77,
                0x2E,
                0x75,
                0x73,
                0x72,
                0x22,
                0x65,
                0x36,
                0xC0,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )
        self._discovery = PrinterDiscovery()

    async def discover_printers_async(
        self,
        timeout_ms: int = 10000,
        idle_timeout_ms: int = 1500,
        max_retries: int = 3,
    ) -> list[FlashForgePrinter]:
        """Discover printers and return the legacy FlashForgePrinter wrapper objects."""
        printers = await self._discovery.discover(
            DiscoveryOptions(
                timeout=timeout_ms,
                idle_timeout=idle_timeout_ms,
                max_retries=max_retries,
            )
        )
        return [FlashForgePrinter.from_discovered_printer(printer) for printer in printers]

    def _parse_printer_response(
        self,
        response: bytes | None,
        ip_address: str,
    ) -> FlashForgePrinter | None:
        if response is None:
            return None

        if LEGACY_PROTOCOL_SIZE <= len(response) < MODERN_PROTOCOL_SIZE and len(response) >= 0x92:
            legacy_name = response[0:32].decode("utf-8", errors="ignore").split("\x00", 1)[0].strip()
            legacy_serial = (
                response[0x92 : 0x92 + 32]
                .decode("utf-8", errors="ignore")
                .split("\x00", 1)[0]
                .strip()
            )
            if legacy_name or legacy_serial:
                return FlashForgePrinter(
                    name=legacy_name,
                    serial_number=legacy_serial,
                    ip_address=ip_address,
                )

        printer = self._discovery.parse_discovery_response(response, ip_address)
        if printer is None:
            return None
        if not printer.name and not printer.serial_number:
            return None
        return FlashForgePrinter.from_discovered_printer(printer)

    def _get_broadcast_addresses(self) -> list[str]:
        return self._discovery.get_broadcast_addresses()

    def _calculate_broadcast_address(self, ip_address: str, subnet_mask: str) -> str | None:
        return self._discovery.calculate_broadcast_address(ip_address, subnet_mask)

    def print_debug_info(self, response: bytes, ip_address: str) -> None:
        print(f"Received response from {ip_address}:")
        print(f"Response length: {len(response)} bytes")
        print("Hex dump:")
        for index in range(0, len(response), 16):
            parts = [f"{index:04x}   "]
            for offset in range(16):
                if index + offset < len(response):
                    parts.append(f"{response[index + offset]:02x} ")
                else:
                    parts.append("   ")
                if offset == 7:
                    parts.append(" ")

            parts.append("  ")
            for offset in range(16):
                if index + offset < len(response):
                    byte = response[index + offset]
                    parts.append(chr(byte) if 32 <= byte <= 126 else ".")
            print("".join(parts))

        print("ASCII dump:")
        print(repr(response.decode("ascii", errors="replace")))


async def _async_main() -> None:
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()
    for printer in printers:
        print(printer)


def main() -> None:
    """CLI entry point for `flashforge-discover`."""
    asyncio.run(_async_main())
