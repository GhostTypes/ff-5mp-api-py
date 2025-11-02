"""
FlashForge Python API - Endstop Status Parser

Parses endstop and machine status information from M119 command responses.
"""
import re
from enum import Enum
from typing import Optional


class MachineStatus(Enum):
    """Enumerates the possible operational statuses of the machine."""
    BUILDING_FROM_SD = "BUILDING_FROM_SD"
    BUILDING_COMPLETED = "BUILDING_COMPLETED"
    PAUSED = "PAUSED"
    READY = "READY"
    BUSY = "BUSY"
    DEFAULT = "DEFAULT"


class MoveMode(Enum):
    """Enumerates the possible movement modes of the printer."""
    MOVING = "MOVING"
    PAUSED = "PAUSED"
    READY = "READY"
    WAIT_ON_TOOL = "WAIT_ON_TOOL"
    HOMING = "HOMING"
    DEFAULT = "DEFAULT"


class Status:
    """
    Represents additional status flags parsed from a status line.
    The meaning of S, L, J, F flags can be specific to printer firmware or model.
    """

    def __init__(self, data: str):
        """
        Creates an instance of Status by parsing a string line.
        It uses regular expressions to find key-value pairs like "S:0".
        
        Args:
            data: The string line containing status flags (e.g., "Status S:0 L:0 J:0 F:0")
        """
        self.s: int = self._get_value(data, "S")
        self.l: int = self._get_value(data, "L")
        self.j: int = self._get_value(data, "J")
        self.f: int = self._get_value(data, "F")

    def _get_value(self, input_str: str, key: str) -> int:
        """
        Helper function to extract a numeric value associated with a key from a string.
        
        Args:
            input_str: The string to search within
            key: The key whose numeric value is to be extracted
            
        Returns:
            The parsed integer value, or -1 if the key is not found or parsing fails
        """
        pattern = rf"{key}:(\d+)"
        match = re.search(pattern, input_str)
        if match and match.group(1):
            return int(match.group(1))
        return -1


class Endstop:
    """
    Represents the state of the printer's endstops.
    Typically, a value of 0 means not triggered, and 1 means triggered.
    """

    def __init__(self, data: str):
        """
        Creates an instance of Endstop by parsing a string line.
        It uses regular expressions to find key-value pairs like "X-max:0".
        
        Args:
            data: The string line containing endstop states (e.g., "Endstop X-max:0 Y-max:0 Z-min:1")
        """
        self.x_max: int = self._get_value(data, "X-max")
        self.y_max: int = self._get_value(data, "Y-max")
        self.z_min: int = self._get_value(data, "Z-min")

    def _get_value(self, input_str: str, key: str) -> int:
        """
        Helper function to extract a numeric value associated with a key from a string.
        
        Args:
            input_str: The string to search within
            key: The key whose numeric value is to be extracted
            
        Returns:
            The parsed integer value, or -1 if the key is not found or parsing fails
        """
        pattern = rf"{key}:(\d+)"
        match = re.search(pattern, input_str)
        if match and match.group(1):
            return int(match.group(1))
        return -1


class EndstopStatus:
    """
    Represents the status of the printer's endstops and various other machine states.
    
    This information is typically parsed from the response of an M119 command or a similar
    consolidated status report from the printer. It includes endstop states, machine operational status,
    movement mode, LED status, and the currently loaded file.
    """

    def __init__(self):
        """Initialize a new EndstopStatus instance."""
        self.endstop: Optional[Endstop] = None
        self.machine_status: MachineStatus = MachineStatus.DEFAULT
        self.move_mode: MoveMode = MoveMode.DEFAULT
        self.status: Optional[Status] = None
        self.led_enabled: bool = False
        self.current_file: Optional[str] = None

    def from_replay(self, replay: str) -> Optional['EndstopStatus']:
        """
        Parses a raw string replay (typically from an M119 or similar status command)
        to populate the properties of this EndstopStatus instance.
        
        The replay is expected to be a multi-line string where each line provides specific information:
        - Line 1 (data[0]): Usually a command echo or header, ignored
        - Line 2 (data[1]): Parsed into the endstop object
        - Line 3 (data[2]): Parsed to determine machine_status by checking for keywords
        - Line 4 (data[3]): Parsed to determine move_mode by checking for keywords
        - Line 5 (data[4]): Parsed into the status object
        - Line 6 (data[5]): Parsed to determine led_enabled (1 for true, 0 for false)
        - Line 7 (data[6]): Parsed to get current_file, or None if empty
        
        Args:
            replay: The raw multi-line string response from the printer
            
        Returns:
            The populated EndstopStatus instance, or None if parsing fails
        """
        if not replay:
            return None

        try:
            data = replay.split('\n')

            # Validate that we have enough lines for a valid response
            # A valid M119 response should have at least 2 lines (command echo + endstop data)
            if len(data) < 2:
                return None

            # Check if the data looks like a valid M119 response
            # Should contain "Endstop" in the second line
            if len(data) > 1 and "Endstop" not in data[1]:
                return None

            # Parse endstop data (line 1)
            if len(data) > 1:
                self.endstop = Endstop(data[1])

            # Parse machine status (line 2)
            if len(data) > 2:
                machine_status = data[2].replace("MachineStatus: ", "").strip()
                if "BUILDING_FROM_SD" in machine_status:
                    self.machine_status = MachineStatus.BUILDING_FROM_SD
                elif "BUILDING_COMPLETED" in machine_status:
                    self.machine_status = MachineStatus.BUILDING_COMPLETED
                elif "PAUSED" in machine_status:
                    self.machine_status = MachineStatus.PAUSED
                elif "READY" in machine_status:
                    self.machine_status = MachineStatus.READY
                elif "BUSY" in machine_status:
                    self.machine_status = MachineStatus.BUSY
                else:
                    print(f"EndstopStatus: Encountered unknown MachineStatus: {machine_status}")
                    self.machine_status = MachineStatus.DEFAULT

            # Parse move mode (line 3)
            if len(data) > 3:
                move_mode = data[3].replace("MoveMode: ", "").strip()
                if "MOVING" in move_mode:
                    self.move_mode = MoveMode.MOVING
                elif "PAUSED" in move_mode:
                    self.move_mode = MoveMode.PAUSED
                elif "READY" in move_mode:
                    self.move_mode = MoveMode.READY
                elif "WAIT_ON_TOOL" in move_mode:
                    self.move_mode = MoveMode.WAIT_ON_TOOL
                elif "HOMING" in move_mode:
                    self.move_mode = MoveMode.HOMING
                else:
                    print(f"EndstopStatus: Encountered unknown MoveMode: {move_mode}")
                    self.move_mode = MoveMode.DEFAULT

            # Parse status flags (line 4)
            if len(data) > 4:
                self.status = Status(data[4])

            # Parse LED status (line 5)
            if len(data) > 5:
                led_str = data[5].replace("LED: ", "").strip()
                try:
                    self.led_enabled = int(led_str) == 1
                except ValueError:
                    self.led_enabled = False

            # Parse current file (line 6)
            if len(data) > 6:
                current_file = data[6].replace("CurrentFile: ", "").strip()
                self.current_file = current_file if current_file else None

            return self

        except Exception as e:
            print("Unable to create EndstopStatus instance from replay")
            print(f"Replay: {replay}")
            print(f"Error: {e}")
            return None

    def is_print_complete(self) -> bool:
        """
        Checks if the machine status indicates that a print has been completed.
        
        Returns:
            True if machine_status is BUILDING_COMPLETED, False otherwise
        """
        return self.machine_status == MachineStatus.BUILDING_COMPLETED

    def is_printing(self) -> bool:
        """
        Checks if the machine status indicates that a print is currently in progress from SD.
        
        Returns:
            True if machine_status is BUILDING_FROM_SD, False otherwise
        """
        return self.machine_status == MachineStatus.BUILDING_FROM_SD

    def is_ready(self) -> bool:
        """
        Checks if the printer is in a ready state (both move mode and machine status are READY).
        
        Returns:
            True if the printer is ready, False otherwise
        """
        return (self.move_mode == MoveMode.READY and
                self.machine_status == MachineStatus.READY)

    def is_paused(self) -> bool:
        """
        Checks if the printer is currently paused (either machine status or move mode is PAUSED).
        
        Returns:
            True if the printer is paused, False otherwise
        """
        return (self.machine_status == MachineStatus.PAUSED or
                self.move_mode == MoveMode.PAUSED)

    def __str__(self) -> str:
        """String representation of the endstop status."""
        return (f"EndstopStatus(machine={self.machine_status.value}, "
                f"move={self.move_mode.value}, led={self.led_enabled}, "
                f"file='{self.current_file}')")

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"EndstopStatus("
                f"endstop={self.endstop}, "
                f"machine_status={self.machine_status}, "
                f"move_mode={self.move_mode}, "
                f"status={self.status}, "
                f"led_enabled={self.led_enabled}, "
                f"current_file='{self.current_file}')")
