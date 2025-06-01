"""
Temperature information parser for FlashForge 3D printers.

This module parses the response from M105 command to extract temperature data
for the extruder and print bed.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TempData:
    """
    Represents temperature data for a single component (e.g., extruder or bed).
    
    Includes current temperature and target (set) temperature.
    Temperatures are stored as strings but can be retrieved as numbers.
    """

    def __init__(self, data: str) -> None:
        """
        Create a TempData instance by parsing a temperature string.
        
        The input string can be in the format "current/set" (e.g., "210/210")
        or just "current" (e.g., "25") if the target temperature is not specified.
        It also handles and removes a trailing "/0.0" if present from some printer firmwares.
        All temperatures are rounded to the nearest integer.
        
        Args:
            data: The temperature data string (e.g., "210/210", "25", "60/60/0.0")
        """
        # Handle potential formatting issues by removing any non-relevant part
        data = data.replace('/0.0', '')  # Remove trailing '/0.0' if exists

        if "/" in data:
            # Replay has current/set temps
            split_temps = data.split('/')
            self._current = self._parse_temp_data(split_temps[0].strip())
            self._set = self._parse_temp_data(split_temps[1].strip()) if len(split_temps) > 1 else None
        else:
            # Replay only has current temp (when printer is idle)
            self._current = self._parse_temp_data(data)
            self._set = None

    def _parse_temp_data(self, data: str) -> str:
        """
        Parse a raw temperature string value, round it, and return as string.
        
        Args:
            data: The raw temperature string (e.g., "210.5", "60")
            
        Returns:
            The rounded temperature as a string
        """
        if "." in data:
            data = data.split('.')[0].strip()  # Truncate decimal part before rounding
        temp = round(float(data))
        return str(temp)

    def get_full(self) -> str:
        """
        Get the full temperature string, including current and set temperatures.
        
        Returns:
            A string in the format "current/set" or just "current" if set temperature is not available
        """
        if self._set is None:
            return self._current
        return f"{self._current}/{self._set}"

    def get_current(self) -> int:
        """
        Get the current temperature as a number.
        
        Returns:
            The current temperature in Celsius
        """
        return int(self._current)

    def get_set(self) -> int:
        """
        Get the target (set) temperature as a number.
        
        Returns:
            The set temperature in Celsius, or 0 if not set
        """
        return int(self._set) if self._set else 0


class TempInfo:
    """
    Represents the temperature information for the printer's extruder and bed.
    
    This data is typically parsed from the response of an M105 G-code command,
    which reports the current and target temperatures.
    """

    def __init__(self) -> None:
        """Initialize empty temperature info."""
        self._extruder_temp: Optional[TempData] = None
        """Temperature data for the extruder."""

        self._bed_temp: Optional[TempData] = None
        """Temperature data for the print bed."""

    def from_replay(self, replay: str) -> Optional['TempInfo']:
        """
        Parse a raw string replay from M105 command to populate temperature info.
        
        The M105 response format is usually a single line (after the "ok" or command echo)
        containing temperature segments like "T0:25/0" or "T:210/210 B:60/60".
        This method splits the relevant line by spaces and then parses each segment.
        It looks for segments starting with "T0:", "T):", or "T:" for extruder temperature,
        and "B:" for bed temperature.
        
        Args:
            replay: The raw multi-line string response from the printer
            
        Returns:
            The populated TempInfo instance, or None if parsing fails
        """
        if not replay:
            return None

        try:
            data = replay.split('\n')
            if len(data) <= 1:
                logger.error(f"TempInfo replay has invalid data: {data}")
                return None

            # Relevant temperature data is usually on the second line (data[1])
            # e.g., "T0:25/0 B:28/0 @:0 B@:0" or "T:210/210 B:60/60"
            temp_data = data[1].split(' ')
            extruder_data_str = None
            bed_data_str = None

            # Parse each temperature segment
            for segment in temp_data:
                # Check for extruder temperature (T0, T, or T) for some printers)
                if segment.startswith('T0:'):
                    extruder_data_str = segment.replace('T0:', '')
                elif segment.startswith('T):'):  # Some printers might use T):
                    extruder_data_str = segment.replace('T):', '')
                elif segment.startswith('T:'):  # General case for T:
                    extruder_data_str = segment.replace('T:', '')
                # Check for bed temperature
                elif segment.startswith('B:'):
                    bed_data_str = segment.replace('B:', '')

            # If we found extruder data, create TempData object
            if extruder_data_str:
                self._extruder_temp = TempData(extruder_data_str)
            else:
                logger.error(f"No extruder temperature found in replay data: {replay}")
                return None  # Extruder temp is critical

            # If we found bed data, create TempData object; otherwise, default to 0/0
            if bed_data_str:
                self._bed_temp = TempData(bed_data_str)
            else:
                logger.warning(f"No bed temperature found in replay data, defaulting to 0/0: {replay}")
                self._bed_temp = TempData('0/0')  # Default if not present

            return self

        except Exception as e:
            logger.error(f"Unable to create TempInfo instance from replay: {e}")
            logger.error(f"Raw replay data: {replay}")
            return None

    def get_extruder_temp(self) -> Optional[TempData]:
        """
        Get the extruder temperature data.
        
        Returns:
            A TempData object for the extruder, or None if not available
        """
        return self._extruder_temp

    def get_bed_temp(self) -> Optional[TempData]:
        """
        Get the print bed temperature data.
        
        Returns:
            A TempData object for the bed, or None if not available
        """
        return self._bed_temp

    def is_cooled(self) -> bool:
        """
        Check if both the bed and extruder are cooled down to relatively low temperatures.
        
        Bed temperature <= 40°C and extruder temperature <= 200°C (though 200 is still hot).
        Use with caution, as "cooled" here is relative and 200C is still very hot for an extruder.
        
        Returns:
            True if temperatures are at or below the defined thresholds, False otherwise
        """
        bed_temp = self._bed_temp.get_current() if self._bed_temp else 0
        extruder_temp = self._extruder_temp.get_current() if self._extruder_temp else 0
        return bed_temp <= 40 and extruder_temp <= 200

    def are_temps_safe(self) -> bool:
        """
        Check if the current temperatures are within a generally safe operating range.
        
        Prevents overheating (extruder < 250°C, bed < 100°C).
        These are arbitrary "safe" limits and might need adjustment based on specific printer/material.
        
        Returns:
            True if temperatures are below the defined "safe" thresholds, False otherwise
        """
        bed_temp = self._bed_temp.get_current() if self._bed_temp else 0
        extruder_temp = self._extruder_temp.get_current() if self._extruder_temp else 0
        return extruder_temp < 250 and bed_temp < 100
