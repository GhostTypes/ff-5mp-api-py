"""
G-code and M-code command constants for FlashForge 3D printers.

This module defines the standard commands used for TCP communication with FlashForge printers.
The '~' prefix is characteristic of FlashForge's TCP command protocol.
Placeholders like '%%filename%%' are intended to be replaced with actual values before sending.
"""

from typing import Final


class GCodes:
    """
    Collection of G-code and M-code command strings for FlashForge 3D printers.
    
    All commands use the FlashForge TCP protocol with '~' prefix.
    """

    # Authentication and session control
    CMD_LOGIN: Final[str] = "~M601 S1"
    """Command to initiate a control session with the printer (login)."""

    CMD_LOGOUT: Final[str] = "~M602"
    """Command to terminate a control session with the printer (logout)."""

    # Emergency control
    CMD_EMERGENCY_STOP: Final[str] = "~M112"
    """Command for an emergency stop of all printer activity."""

    # Status queries
    CMD_PRINT_STATUS: Final[str] = "~M27"
    """Command to request the current print job status."""

    CMD_ENDSTOP_INFO: Final[str] = "~M119"
    """Command to request the status of the printer's endstops."""

    CMD_INFO_STATUS: Final[str] = "~M115"
    """Command to request general printer information, including firmware version."""

    CMD_INFO_XYZAB: Final[str] = "~M114"
    """Command to request the current X, Y, Z, A, B coordinates of the print head."""

    CMD_TEMP: Final[str] = "~M105"
    """Command to request current temperatures (extruder, bed)."""

    # LED control
    CMD_LED_ON: Final[str] = "~M146 r255 g255 b255 F0"
    """Command to turn the printer's LED lights on (full white)."""

    CMD_LED_OFF: Final[str] = "~M146 r0 g0 b0 F0"
    """Command to turn the printer's LED lights off."""

    # Filament runout sensor
    CMD_RUNOUT_SENSOR_ON: Final[str] = "~M405"
    """Command to enable the filament runout sensor."""

    CMD_RUNOUT_SENSOR_OFF: Final[str] = "~M406"
    """Command to disable the filament runout sensor."""

    # File operations
    CMD_LIST_LOCAL_FILES: Final[str] = "~M661"
    """Command to list files stored locally on the printer."""

    CMD_GET_THUMBNAIL: Final[str] = "~M662"
    """Command to retrieve a thumbnail image for a specified G-code file."""

    # Camera control
    TAKE_PICTURE: Final[str] = "~M240"
    """Command to instruct the printer to take a picture with its camera, if equipped."""

    # Movement and homing
    CMD_HOME_AXES: Final[str] = "~G28"
    """Command to home all printer axes (X, Y, Z)."""

    # Print job control
    CMD_START_PRINT: Final[str] = "~M23 0:/user/%%filename%%"
    """Command to select a file for printing. %%filename%% should be replaced with actual file path."""

    CMD_PAUSE_PRINT: Final[str] = "~M25"
    """Command to pause the current print job."""

    CMD_RESUME_PRINT: Final[str] = "~M24"
    """Command to resume a paused print job."""

    CMD_STOP_PRINT: Final[str] = "~M26"
    """Command to stop/cancel the current print job."""

    # Temperature control with waiting
    WAIT_FOR_HOTEND_TEMP: Final[str] = "~M109"
    """Command to set extruder temperature and wait until it's reached. Requires S[temperature] parameter."""

    WAIT_FOR_BED_TEMP: Final[str] = "~M190"
    """Command to set bed temperature and wait until it's reached. Requires S[temperature] or R[temperature] parameter."""
