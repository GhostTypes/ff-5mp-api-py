"""
Location information parser for FlashForge 3D printers.

This module parses the response from M114 command to extract current
X, Y, Z coordinates of the printer's print head.
"""

import logging
import re
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

    def from_replay(self, replay: str) -> Optional["LocationInfo"]:
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
            lines = [line.strip() for line in replay.replace("\r", "\n").split("\n") if line.strip()]
            coordinate_line = next(
                (line for line in lines if "X:" in line and "Y:" in line and "Z:" in line),
                "",
            )
            if not coordinate_line:
                logger.error("LocationInfo replay has bad/null data")
                return None

            x_match = re.search(r"X:\s*([^\s]+)", coordinate_line)
            y_match = re.search(r"Y:\s*([^\s]+)", coordinate_line)
            z_match = re.search(r"Z:\s*([^\s]+)", coordinate_line)
            if not x_match or not y_match or not z_match:
                logger.error("LocationInfo replay has bad/null data")
                return None

            self.x = x_match.group(1)
            self.y = y_match.group(1)
            self.z = z_match.group(1)
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
