"""
FlashForge Python API - Printer Discovery (FIXED VERSION)

UDP-based printer discovery implementation that finds FlashForge printers on the local network.
Fixed to match the original TypeScript implementation behavior.
"""
import asyncio
import logging
import socket
from dataclasses import dataclass
from typing import List, Optional

import netifaces

logger = logging.getLogger(__name__)


@dataclass
class FlashForgePrinter:
    """
    Represents a discovered FlashForge 3D printer.
    Stores information such as name, serial number, and IP address.
    """
    name: str = ""
    serial_number: str = ""
    ip_address: str = ""

    def __str__(self) -> str:
        """Returns a string representation of the FlashForgePrinter object."""
        return f"Name: {self.name}, Serial: {self.serial_number}, IP: {self.ip_address}"

    def __repr__(self) -> str:
        """Returns a detailed string representation for debugging."""
        return f"FlashForgePrinter(name='{self.name}', serial_number='{self.serial_number}', ip_address='{self.ip_address}')"


class FlashForgePrinterDiscovery:
    """
    Handles the discovery of FlashForge printers on the local network.
    Uses UDP broadcast messages to find printers and parses their responses.
    """

    # The UDP port used for sending discovery messages to FlashForge printers
    DISCOVERY_PORT = 48899
    # The port we listen on for responses (must match TypeScript implementation)
    LISTEN_PORT = 18007

    def __init__(self):
        """Initialize the printer discovery client."""
        self.discovery_port = self.DISCOVERY_PORT
        self.listen_port = self.LISTEN_PORT

        # The discovery UDP packet is a 20-byte message.
        # It starts with "www.usr" followed by specific bytes.
        # This packet structure is based on observations from FlashPrint software.
        self.discovery_message = bytes([
            0x77, 0x77, 0x77, 0x2e, 0x75, 0x73, 0x72, 0x22,  # "www.usr"
            0x65, 0x36, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00
        ])

    async def discover_printers_async(
        self,
        timeout_ms: int = 10000,
        idle_timeout_ms: int = 1500,
        max_retries: int = 3
    ) -> List[FlashForgePrinter]:
        """
        Discovers FlashForge printers on the network asynchronously.
        
        FIXED VERSION - Uses proper asyncio UDP socket handling that matches the TypeScript implementation.
        
        Args:
            timeout_ms: The total time (in milliseconds) to wait for printer responses
            idle_timeout_ms: The time (in milliseconds) to wait for additional responses 
                           after the last received one
            max_retries: The maximum number of discovery attempts
            
        Returns:
            A list of FlashForgePrinter objects found on the network
        """
        printers: List[FlashForgePrinter] = []
        broadcast_addresses = self._get_broadcast_addresses()
        attempt = 0

        logger.info(f"Starting printer discovery with {len(broadcast_addresses)} broadcast addresses")

        while attempt < max_retries:
            attempt += 1
            logger.debug(f"Discovery attempt {attempt}/{max_retries}")

            try:
                # Use asyncio datagram endpoint for proper UDP handling
                transport, protocol = await asyncio.get_event_loop().create_datagram_endpoint(
                    lambda: DiscoveryProtocol(self),
                    local_addr=('0.0.0.0', self.listen_port),
                    allow_broadcast=True
                )

                try:
                    # Send discovery messages to all broadcast addresses
                    for broadcast_address in broadcast_addresses:
                        try:
                            transport.sendto(self.discovery_message, (broadcast_address, self.discovery_port))
                            logger.debug(f"Sent discovery message to {broadcast_address}:{self.discovery_port}")
                        except Exception as e:
                            logger.warning(f"Failed to send to {broadcast_address}: {e}")

                    # Wait for responses using the protocol
                    found_printers = await protocol.wait_for_responses(
                        timeout_ms / 1000.0, idle_timeout_ms / 1000.0
                    )
                    printers.extend(found_printers)

                finally:
                    transport.close()

                if printers:
                    break  # Printers found, exit retry loop

                if attempt < max_retries:
                    logger.debug(f"No printers found, waiting before retry {attempt + 1}")
                    await asyncio.sleep(1.0)  # Wait before retrying

            except Exception as e:
                logger.error(f"Error during discovery attempt {attempt}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1.0)

        # Remove duplicates based on IP address
        unique_printers = {}
        for printer in printers:
            if printer.ip_address not in unique_printers:
                unique_printers[printer.ip_address] = printer

        final_printers = list(unique_printers.values())
        logger.info(f"Discovery completed. Found {len(final_printers)} unique printers")

        return final_printers

    def _parse_printer_response(self, response: bytes, ip_address: str) -> Optional[FlashForgePrinter]:
        """
        Parses the UDP response received from a FlashForge printer.
        
        The response is a buffer containing printer information at specific offsets:
        - Printer Name: ASCII string at offset 0x00 (32 bytes)
        - Serial Number: ASCII string at offset 0x92 (32 bytes)
        
        Args:
            response: The bytes containing the printer's response
            ip_address: The IP address from which the response was received
            
        Returns:
            A FlashForgePrinter object if parsing is successful, otherwise None
        """
        # Expected response length is at least 0xC4 (196 bytes) to contain name and serial
        if not response:
            logger.warning(f"Invalid response from {ip_address}: response is None or empty")
            return None

        if len(response) < 0xC4:
            logger.warning(f"Invalid response from {ip_address}, length: {len(response)}")
            return None

        try:
            # Printer name is at offset 0x00, padded with null characters
            name = response[0:32].decode('ascii', errors='ignore').rstrip('\x00')

            # Serial number is at offset 0x92, padded with null characters
            serial_number = response[0x92:0x92 + 32].decode('ascii', errors='ignore').rstrip('\x00')

            if not name and not serial_number:
                logger.warning(f"Empty name and serial from {ip_address}")
                return None

            printer = FlashForgePrinter(
                name=name,
                serial_number=serial_number,
                ip_address=ip_address
            )

            return printer

        except Exception as e:
            logger.error(f"Error parsing response from {ip_address}: {e}")
            return None

    def _get_broadcast_addresses(self) -> List[str]:
        """
        Retrieves a list of broadcast addresses for all active IPv4 network interfaces.
        
        Returns:
            A list of broadcast address strings
        """
        broadcast_addresses: List[str] = []

        try:
            # Get all network interfaces
            for interface_name in netifaces.interfaces():
                try:
                    # Get IPv4 addresses for this interface
                    addresses = netifaces.ifaddresses(interface_name)
                    if netifaces.AF_INET not in addresses:
                        continue

                    for addr_info in addresses[netifaces.AF_INET]:
                        # Skip loopback interfaces
                        if addr_info.get('addr', '').startswith('127.'):
                            continue

                        # Calculate broadcast address if netmask is available
                        ip_addr = addr_info.get('addr')
                        netmask = addr_info.get('netmask')

                        if ip_addr and netmask:
                            broadcast = self._calculate_broadcast_address(ip_addr, netmask)
                            if broadcast and broadcast not in broadcast_addresses:
                                broadcast_addresses.append(broadcast)
                                logger.debug(f"Added broadcast address: {broadcast} (interface: {interface_name})")

                except Exception as e:
                    logger.warning(f"Error processing interface {interface_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}")
            # Fallback to common broadcast addresses
            broadcast_addresses = ['255.255.255.255', '192.168.1.255', '192.168.0.255']
            logger.info("Using fallback broadcast addresses")

        # Always include the general broadcast address
        if '255.255.255.255' not in broadcast_addresses:
            broadcast_addresses.append('255.255.255.255')

        logger.debug(f"Using broadcast addresses: {broadcast_addresses}")
        return broadcast_addresses

    def _calculate_broadcast_address(self, ip_address: str, subnet_mask: str) -> Optional[str]:
        """
        Calculates the broadcast address for a given IP address and subnet mask.
        
        Args:
            ip_address: The IPv4 address string (e.g., "192.168.1.10")
            subnet_mask: The IPv4 subnet mask string (e.g., "255.255.255.0")
            
        Returns:
            The calculated broadcast address string, or None if input is invalid
        """
        try:
            # Convert IP and subnet to arrays of numbers
            ip_parts = [int(x) for x in ip_address.split('.')]
            mask_parts = [int(x) for x in subnet_mask.split('.')]

            if len(ip_parts) != 4 or len(mask_parts) != 4:
                return None

            # Calculate broadcast address: IP | (~MASK)
            broadcast_parts = [ip_parts[i] | (~mask_parts[i] & 255) for i in range(4)]
            return '.'.join(map(str, broadcast_parts))

        except Exception as e:
            logger.warning(f"Error calculating broadcast address for {ip_address}/{subnet_mask}: {e}")
            return None

    def print_debug_info(self, response: bytes, ip_address: str) -> None:
        """
        Prints detailed debugging information about a received UDP response.
        
        Args:
            response: The bytes containing the response data
            ip_address: The IP address from which the response was received
        """
        print(f"Received response from {ip_address}:")
        print(f"Response length: {len(response)} bytes")

        # Hex dump
        print("Hex dump:")
        for i in range(0, len(response), 16):
            line = f"{i:04x}   "

            # Hex values
            for j in range(16):
                if i + j < len(response):
                    line += f"{response[i + j]:02x} "
                else:
                    line += "   "

                if j == 7:
                    line += " "

            # ASCII representation
            line += "  "
            for j in range(16):
                if i + j < len(response):
                    c = response[i + j]
                    line += chr(c) if 32 <= c <= 126 else '.'

            print(line)

        # ASCII dump
        print("ASCII dump:")
        try:
            ascii_content = response.decode('ascii', errors='replace')
            print(repr(ascii_content))
        except Exception as e:
            print(f"Error decoding ASCII: {e}")


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """
    Asyncio datagram protocol for handling UDP discovery responses.
    This matches the event-driven approach used in the TypeScript implementation.
    """

    def __init__(self, discovery: FlashForgePrinterDiscovery):
        self.discovery = discovery
        self.printers: List[FlashForgePrinter] = []
        self.response_event = asyncio.Event()
        self.last_response_time = 0.0

    def connection_made(self, transport):
        self.transport = transport
        logger.debug("Discovery protocol connection established")

    def datagram_received(self, data: bytes, addr):
        """Handle incoming UDP datagram (printer response)."""
        ip_address = addr[0]
        logger.debug(f"Received {len(data)} bytes from {ip_address}")

        # Parse the response
        printer = self.discovery._parse_printer_response(data, ip_address)
        if printer:
            self.printers.append(printer)
            logger.info(f"Discovered printer: {printer}")

        # Update last response time and signal that we got a response
        self.last_response_time = asyncio.get_event_loop().time()
        self.response_event.set()
        self.response_event.clear()  # Reset for next response

    def error_received(self, exc):
        logger.error(f"Discovery protocol error: {exc}")

    async def wait_for_responses(self, total_timeout: float, idle_timeout: float) -> List[FlashForgePrinter]:
        """
        Wait for printer responses with total and idle timeouts.
        
        Args:
            total_timeout: Maximum total time to wait for responses
            idle_timeout: Maximum time to wait between responses
            
        Returns:
            List of discovered printers
        """
        start_time = asyncio.get_event_loop().time()
        self.last_response_time = start_time

        logger.debug(f"Waiting for responses (total timeout: {total_timeout}s, idle timeout: {idle_timeout}s)")

        while True:
            current_time = asyncio.get_event_loop().time()

            # Check total timeout
            if current_time - start_time >= total_timeout:
                logger.debug("Total timeout reached")
                break

            # Check idle timeout
            if current_time - self.last_response_time >= idle_timeout:
                logger.debug("Idle timeout reached")
                break

            # Wait for next response or timeout
            try:
                remaining_total = total_timeout - (current_time - start_time)
                remaining_idle = idle_timeout - (current_time - self.last_response_time)
                wait_time = min(remaining_total, remaining_idle, 0.1)  # Max 100ms wait
                
                if wait_time <= 0:
                    break
                    
                await asyncio.wait_for(self.response_event.wait(), timeout=wait_time)
            except asyncio.TimeoutError:
                # Continue to check timeouts
                continue

        logger.debug(f"Finished waiting, found {len(self.printers)} printers")
        return self.printers
