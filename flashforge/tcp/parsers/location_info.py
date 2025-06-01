"""
Location information parser for FlashForge 3D printers.

This module parses the response from M114 command to extract current
X, Y, Z coordinates of the printer's print head.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LocationInfo:
    """
    Represents the current X, Y, and Z coordinates of the printer's print head.
    
    This information is typically parsed from the response of an M114 G-code command,
    which reports the current position.
    """

    def __init__(self) -> None:
        """Initialize empty location info."""
        self.x: str = ""
        """The current X-axis coordinate as a string (e.g., "10.00")."""

        self.y: str = ""
        """The current Y-axis coordinate as a string (e.g., "20.50")."""

        self.z: str = ""
        """The current Z-axis coordinate as a string (e.g., "5.25")."""

    def from_replay(self, replay: str) -> Optional['LocationInfo']:
        """
        Parse a raw string replay from M114 command to populate coordinate info.
        
        The parsing logic assumes the replay is a multi-line string where the second line
        (data[1]) contains the coordinate data in a format like "X:10.00 Y:20.50 Z:5.25 ...".
        It splits this line by spaces and then extracts the values for X, Y, and Z by
        removing the prefixes "X:", "Y:", and "Z:".
        
        Args:
            replay: The raw multi-line string response from the printer
            
        Returns:
            The populated LocationInfo instance, or None if parsing fails
        """
        try:
            data = replay.split('\n')
            # The first line (data[0]) is often the command echo (e.g., "ok M114") or similar,
            # actual coordinate data is expected on the second line.
            loc_data = data[1].split(' ')
            self.x = loc_data[0].replace("X:", "").strip()
            self.y = loc_data[1].replace("Y:", "").strip()
            self.z = loc_data[2].replace("Z:", "").strip()
            return self
        except Exception:
            logger.error("LocationInfo replay has bad/null data")
            return None

    def __str__(self) -> str:
        """
        Return a string representation of the location information.
        
        Returns:
            A string in the format "X: [X_value] Y: [Y_value] Z: [Z_value]"
        """
        return f"X: {self.x} Y: {self.y} Z: {self.z}"
