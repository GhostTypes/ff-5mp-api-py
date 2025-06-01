"""
Printer information parser for FlashForge 3D printers.

This module parses the response from M115 command to extract printer details
like model, firmware version, serial number, and capabilities.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PrinterInfo:
    """
    Represents general information about the FlashForge 3D printer.
    
    This information is typically parsed from the response of an M115 G-code command,
    which provides details about the printer's firmware and capabilities.
    """

    def __init__(self) -> None:
        """Initialize empty printer info."""
        self.type_name: str = ""
        """The machine type or model name (e.g., "FlashForge Adventurer 5M Pro")."""

        self.name: str = ""
        """The user-assigned name of the printer."""

        self.firmware_version: str = ""
        """The firmware version currently installed on the printer."""

        self.serial_number: str = ""
        """The unique serial number of the printer."""

        self.dimensions: str = ""
        """The build dimensions of the printer (e.g., "X:220 Y:220 Z:220")."""

        self.mac_address: str = ""
        """The MAC address of the printer's network interface."""

        self.tool_count: str = ""
        """The number of tools (extruders) the printer has."""

    def from_replay(self, replay: str) -> Optional['PrinterInfo']:
        """
        Parse a raw string replay from M115 command to populate printer info.
        
        The M115 response is expected to be a multi-line string where each line
        provides a piece of information in a "Key: Value" format.
        
        Expected format:
        - Line 1: Command echo/header (ignored)
        - Line 2: "Machine Type: [TypeName]"
        - Line 3: "Machine Name: [Name]"
        - Line 4: "Firmware: [FirmwareVersion]"
        - Line 5: "SN: [SerialNumber]"
        - Line 6: Dimensions string (e.g., "X:220 Y:220 Z:220")
        - Line 7: "Tool count: [ToolCount]"
        - Line 8: "Mac Address:[MacAddress]"
        
        Args:
            replay: The raw multi-line string response from the M115 command
            
        Returns:
            The populated PrinterInfo instance, or None if parsing fails
        """
        if not replay:
            return None

        try:
            data = replay.split('\n')

            # Parse machine type (line 2)
            name = self._get_right(data[1])  # Expected: "Machine Type: Adventurer 5M Pro"
            if name is None:
                logger.error("PrinterInfo replay has null Machine Type")
                return None
            self.type_name = name

            # Parse machine name (line 3)
            nick = self._get_right(data[2])  # Expected: "Machine Name: MyPrinter"
            if nick is None:
                logger.error("PrinterInfo replay has null Machine Name")
                return None
            self.name = nick

            # Parse firmware version (line 4)
            fw = self._get_right(data[3])  # Expected: "Firmware: V1.2.3"
            if fw is None:
                logger.error("PrinterInfo replay has null firmware version")
                return None
            self.firmware_version = fw

            # Parse serial number (line 5)
            sn = self._get_right(data[4])  # Expected: "SN: SN12345"
            if sn is None:
                logger.error("PrinterInfo replay has null serial number")
                return None
            self.serial_number = sn

            # Parse dimensions (line 6) - direct string
            if len(data) > 5:
                self.dimensions = data[5].strip()  # Expected: "X:220 Y:220 Z:220"

            # Parse tool count (line 7)
            if len(data) > 6:
                tcs = self._get_right(data[6])  # Expected: "Tool count: 1"
                if tcs is None:
                    logger.error("PrinterInfo replay has null tool count")
                    return None
                self.tool_count = tcs

            # Parse MAC address (line 8)
            if len(data) > 7:
                self.mac_address = data[7].replace("Mac Address:", "").strip()

            return self

        except Exception as e:
            logger.error(f"Error creating PrinterInfo instance from replay: {e}")
            return None

    def _get_right(self, rp_data: str) -> Optional[str]:
        """
        Helper function to extract the value part of a "Key: Value" string.
        
        Args:
            rp_data: The input string (e.g., "Machine Type: Adventurer 5M Pro")
            
        Returns:
            The extracted value string (e.g., "Adventurer 5M Pro"), or None if parsing fails
        """
        try:
            return rp_data.split(':', 1)[1].strip()
        except (IndexError, AttributeError):
            return None

    def __str__(self) -> str:
        """
        Return a string representation of the printer information.
        
        Returns:
            A multi-line string detailing the printer's properties
        """
        return (
            f"Printer Type: {self.type_name}\n"
            f"Name: {self.name}\n"
            f"Firmware: {self.firmware_version}\n"
            f"Serial Number: {self.serial_number}\n"
            f"Print Dimensions: {self.dimensions}\n"
            f"Tool Count: {self.tool_count}\n"
            f"MAC Address: {self.mac_address}"
        )
