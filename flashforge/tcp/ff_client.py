"""
High-level client for FlashForge 3D printers via TCP/IP.

This module provides a comprehensive interface for interacting with FlashForge printers,
building upon the basic TCP communication provided by FlashForgeTcpClient.
"""

import asyncio
import logging
from typing import Optional

from .gcode import GCodeController, GCodes
from .parsers import EndstopStatus, LocationInfo, PrinterInfo, PrintStatus, TempInfo, ThumbnailInfo
from .tcp_client import FlashForgeTcpClient

logger = logging.getLogger(__name__)


class FlashForgeClient(FlashForgeTcpClient):
    """
    High-level client for interacting with FlashForge 3D printers via TCP/IP.
    
    This class implements specific G-code commands and workflows for printer control,
    such as initialization, LED control, job management, homing, temperature settings,
    filament operations, and retrieving various printer statuses.
    
    It uses a "legacy" API approach primarily based on sending G-code/M-code commands
    and parsing text-based responses.
    """

    def __init__(self, hostname: str) -> None:
        """
        Create an instance of FlashForgeClient.
        
        Args:
            hostname: The IP address or hostname of the FlashForge printer
        """
        super().__init__(hostname)
        self._control = GCodeController(self)
        self._is_5m_pro = False
        """Flag indicating if the connected printer is a 5M Pro model, which may have specific features."""

    def get_ip(self) -> str:
        """
        Get the IP address or hostname of the connected printer.
        
        Returns:
            The printer's hostname or IP address
        """
        return self.hostname

    def gcode(self) -> GCodeController:
        """
        Get the GCodeController instance associated with this client.
        
        Provides access to specific G-code command methods.
        
        Returns:
            The GCodeController instance
        """
        return self._control

    async def init_control(self) -> bool:
        """
        Initialize the control connection with the printer.
        
        This typically involves sending a login command, retrieving printer info,
        and starting a keep-alive mechanism. Retries on failure.
        
        Returns:
            True if control is successfully initialized, False otherwise
        """
        logger.info("(Legacy API) InitControl()")
        tries = 0
        while tries <= 3:
            result = await self.send_raw_cmd(GCodes.CMD_LOGIN)
            if result and "Control failed." not in result and "ok" in result:
                await asyncio.sleep(0.1)
                info = await self.get_printer_info()
                if not info:
                    logger.info("(Legacy API) Failed to get printer info, aborting.")
                    return False

                logger.info(f"(Legacy API) connected to: {info.type_name}")
                logger.info(f"(Legacy API) Firmware version: {info.firmware_version}")

                if "5M" in info.type_name and "Pro" in info.type_name:
                    self._is_5m_pro = True

                await self.start_keep_alive()
                return True

            tries += 1
            # Ensures no errors from previous connections that were improperly closed
            await self.send_raw_cmd(GCodes.CMD_LOGOUT)
            await asyncio.sleep(0.5 * tries)

        return False

    async def led_on(self) -> bool:
        """
        Turn the printer's LED lights on.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.led_on()

    async def led_off(self) -> bool:
        """
        Turn the printer's LED lights off.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.led_off()

    async def pause_job(self) -> bool:
        """
        Pause the current print job.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.pause_job()

    async def resume_job(self) -> bool:
        """
        Resume a paused print job.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.resume_job()

    async def stop_job(self) -> bool:
        """
        Stop the current print job.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.stop_job()

    async def start_job(self, name: str) -> bool:
        """
        Start a print job from a file stored on the printer.
        
        Args:
            name: The name of the file to print (typically without path)
            
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.start_job(name)

    async def home_axes(self) -> bool:
        """
        Home all axes (X, Y, Z) of the printer.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.home()

    async def rapid_home(self) -> bool:
        """
        Perform a rapid homing of all axes.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.rapid_home()

    async def turn_runout_sensor_on(self) -> bool:
        """
        Turn on the filament runout sensor.
        
        This functionality is only available on specific printer models (e.g., 5M Pro).
        
        Returns:
            True if the command is successful and applicable, False otherwise
        """
        if self._is_5m_pro:
            return await self.send_cmd_ok(GCodes.CMD_RUNOUT_SENSOR_ON)

        logger.info("Filament runout sensor not equipped on this printer.")
        return False

    async def turn_runout_sensor_off(self) -> bool:
        """
        Turn off the filament runout sensor.
        
        This functionality is only available on specific printer models (e.g., 5M Pro).
        
        Returns:
            True if the command is successful and applicable, False otherwise
        """
        if self._is_5m_pro:
            return await self.send_cmd_ok(GCodes.CMD_RUNOUT_SENSOR_OFF)

        logger.info("Filament runout sensor not equipped on this printer.")
        return False

    async def set_extruder_temp(self, temp: int, wait_for: bool = False) -> bool:
        """
        Set the target temperature for the extruder.
        
        Args:
            temp: The target temperature in Celsius
            wait_for: If True, the method will wait until the target temperature is reached
            
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.set_extruder_temp(temp, wait_for)

    async def cancel_extruder_temp(self) -> bool:
        """
        Cancel extruder heating and set its target temperature to 0.
        
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.cancel_extruder_temp()

    async def set_bed_temp(self, temp: int, wait_for: bool = False) -> bool:
        """
        Set the target temperature for the print bed.
        
        Args:
            temp: The target temperature in Celsius
            wait_for: If True, the method will wait until the target temperature is reached
            
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.set_bed_temp(temp, wait_for)

    async def cancel_bed_temp(self, wait_for_cool: bool = False) -> bool:
        """
        Cancel print bed heating and set its target temperature to 0.
        
        Args:
            wait_for_cool: If True, waits for the bed to cool down after canceling
            
        Returns:
            True if the command is successful, False otherwise
        """
        return await self._control.cancel_bed_temp(wait_for_cool)

    async def extrude(self, length: float, feedrate: int = 450) -> bool:
        """
        Command the extruder to extrude a specific length of filament.
        
        Uses G1 E[length] F[feedrate] command.
        
        Args:
            length: The length of filament to extrude in millimeters
            feedrate: The feedrate for extrusion in mm/min (default: 450)
            
        Returns:
            True if the command is successful, False otherwise
        """
        return await self.send_cmd_ok(f"~G1 E{length} F{feedrate}")

    async def move_extruder(self, x: float, y: float, feedrate: int) -> bool:
        """
        Move the extruder to a specified X, Y position.
        
        Uses G1 X[x] Y[y] F[feedrate] command.
        
        Args:
            x: The target X coordinate
            y: The target Y coordinate
            feedrate: The feedrate for the movement in mm/min
            
        Returns:
            True if the command is successful, False otherwise
        """
        return await self.send_cmd_ok(f"~G1 X{x} Y{y} F{feedrate}")

    async def move(self, x: float, y: float, z: float, feedrate: int) -> bool:
        """
        Move the extruder to a specified X, Y, Z position.
        
        Uses G1 X[x] Y[y] Z[z] F[feedrate] command.
        
        Args:
            x: The target X coordinate
            y: The target Y coordinate
            z: The target Z coordinate
            feedrate: The feedrate for the movement in mm/min
            
        Returns:
            True if the command is successful, False otherwise
        """
        return await self.send_cmd_ok(f"~G1 X{x} Y{y} Z{z} F{feedrate}")

    async def send_cmd_ok(self, cmd: str) -> bool:
        """
        Send a G-code/M-code command to the printer and check for an "ok" response.
        
        Expects the printer's reply to include "Received." and "ok" to be considered successful.
        
        Args:
            cmd: The command string to send (e.g., "~M115")
            
        Returns:
            True if the command is acknowledged with "ok", False otherwise or on error
        """
        try:
            reply = await self.send_command_async(cmd)
            if reply and "Received." in reply and "ok" in reply:
                return True
        except Exception as ex:
            logger.error(f"SendCmdOk exception sending cmd: {cmd} : {ex}")
            return False
        return False

    async def send_raw_cmd(self, cmd: str) -> str:
        """
        Send a raw command string to the printer and return the raw response.
        
        Handles a special case for "M661" (list files), which is processed differently.
        
        Args:
            cmd: The raw command string to send
            
        Returns:
            The printer's raw string response, or an empty string on failure.
            For "M661", it returns a newline-separated list of files.
        """
        if "M661" not in cmd:
            result = await self.send_command_async(cmd)
            return result or ''

        file_list = await self.get_file_list_async()
        return "\n".join(file_list)

    async def get_printer_info(self) -> Optional[PrinterInfo]:
        """
        Retrieve general printer information (model, firmware, etc.).
        
        Sends CMD_INFO_STATUS and parses the response into a PrinterInfo object.
        
        Returns:
            A PrinterInfo object, or None if retrieval fails
        """
        response = await self.send_command_async(GCodes.CMD_INFO_STATUS)
        if response:
            return PrinterInfo().from_replay(response)
        return None

    async def get_temp_info(self) -> Optional[TempInfo]:
        """
        Retrieve current temperature information (extruder, bed).
        
        Sends CMD_TEMP and parses the response into a TempInfo object.
        
        Returns:
            A TempInfo object, or None if retrieval fails
        """
        response = await self.send_command_async(GCodes.CMD_TEMP)
        if response:
            return TempInfo().from_replay(response)
        return None

    async def get_location_info(self) -> Optional[LocationInfo]:
        """
        Retrieve the current XYZ coordinates of the print head.
        
        Sends CMD_INFO_XYZAB and parses the response into a LocationInfo object.
        
        Returns:
            A LocationInfo object, or None if retrieval fails
        """
        response = await self.send_command_async(GCodes.CMD_INFO_XYZAB)
        if response:
            return LocationInfo().from_replay(response)
        return None

    async def _get_nozzle_temp(self) -> float:
        """
        Retrieve the current temperature of the nozzle (extruder).
        
        Returns:
            The current nozzle temperature in Celsius, or 0 if unavailable
        """
        temps = await self.get_temp_info()
        if temps and temps.get_extruder_temp():
            return temps.get_extruder_temp().get_current()
        return 0.0

    async def get_endstop_status(self) -> Optional[EndstopStatus]:
        """
        Retrieve the current endstop status and machine state information.
        
        Sends M119 command and parses the response into an EndstopStatus object.
        This includes endstop states, machine status, move mode, LED status, and current file.
        
        Returns:
            An EndstopStatus object, or None if retrieval fails
        """
        response = await self.send_command_async(GCodes.CMD_INFO_STATUS)  # M119
        if response:
            return EndstopStatus().from_replay(response)
        return None

    async def get_print_status(self) -> Optional[PrintStatus]:
        """
        Retrieve the current print status and progress information.
        
        Sends M27 command and parses the response into a PrintStatus object.
        This includes SD card byte progress and layer progress.
        
        Returns:
            A PrintStatus object, or None if retrieval fails
        """
        response = await self.send_command_async("~M27")  # Print progress
        if response:
            return PrintStatus().from_replay(response)
        return None

    async def get_thumbnail(self, file_name: str) -> Optional[ThumbnailInfo]:
        """
        Retrieve the thumbnail image for a specific file.
        
        Sends M662 command and parses the response to extract PNG thumbnail data.
        
        Args:
            file_name: The name of the file to get the thumbnail for
            
        Returns:
            A ThumbnailInfo object containing the PNG image data, or None if retrieval fails
        """
        # M662 command to get thumbnail
        cmd = f"~M662 {file_name}"
        response = await self.send_command_async(cmd)
        if response:
            return ThumbnailInfo().from_replay(response, file_name)
        return None

    async def check_machine_state(self) -> str:
        """
        Get a simplified machine state string for quick status checking.
        
        Returns:
            A string indicating the machine state ("printing", "ready", "paused", "complete", "unknown")
        """
        endstop_status = await self.get_endstop_status()
        if not endstop_status:
            return "unknown"

        if endstop_status.is_printing():
            return "printing"
        elif endstop_status.is_print_complete():
            return "complete"
        elif endstop_status.is_paused():
            return "paused"
        elif endstop_status.is_ready():
            return "ready"
        else:
            return "unknown"

    async def get_current_print_file(self) -> Optional[str]:
        """
        Get the name of the currently loaded/printing file.
        
        Returns:
            The filename of the current print job, or None if no file is loaded
        """
        endstop_status = await self.get_endstop_status()
        if endstop_status:
            return endstop_status.current_file
        return None

    async def is_printer_ready(self) -> bool:
        """
        Check if the printer is ready for new commands.
        
        Returns:
            True if the printer is in a ready state, False otherwise
        """
        endstop_status = await self.get_endstop_status()
        if endstop_status:
            return endstop_status.is_ready()
        return False

    async def get_print_progress(self) -> tuple[int, int, int]:
        """
        Get comprehensive print progress information.
        
        Returns:
            A tuple of (layer_percent, sd_percent, current_layer) where:
            - layer_percent: Progress based on layers (0-100)
            - sd_percent: Progress based on SD card bytes (0-100)
            - current_layer: Current layer number
            Returns (0, 0, 0) if progress information is unavailable
        """
        print_status = await self.get_print_status()
        if not print_status:
            return (0, 0, 0)

        layer_percent = print_status.get_print_percent()
        sd_percent = print_status.get_sd_percent()

        # Handle NaN values
        if layer_percent != layer_percent:  # NaN check
            layer_percent = 0
        if sd_percent != sd_percent:  # NaN check
            sd_percent = 0

        try:
            current_layer = int(print_status.layer_current) if print_status.layer_current else 0
        except ValueError:
            current_layer = 0

        return (int(layer_percent), int(sd_percent), current_layer)

    async def wait_for_part_cool(self, target_temp: float = 50.0, timeout_seconds: int = 1800) -> bool:
        """
        Wait for printer components (extruder and bed) to cool down to a safe temperature.
        
        This method cancels heating for both extruder and bed, then waits for them to cool down.
        
        Args:
            target_temp: The target temperature to wait for (default: 50°C)
            timeout_seconds: Maximum time to wait in seconds (default: 30 minutes)
            
        Returns:
            True if components cooled to target temperature, False if timeout or error
        """
        logger.info(f"Starting cooling process - waiting for parts to cool to {target_temp}°C")
        
        # Cancel heating for both extruder and bed
        extruder_cancel_ok = await self.cancel_extruder_temp()
        bed_cancel_ok = await self.cancel_bed_temp()
        
        if not (extruder_cancel_ok and bed_cancel_ok):
            logger.error("Failed to cancel heating - cannot wait for cooling")
            return False
        
        start_time = asyncio.get_event_loop().time()
        timeout_time = start_time + timeout_seconds
        
        extruder_cooled = False
        bed_cooled = False
        
        while asyncio.get_event_loop().time() < timeout_time:
            # Check current temperatures
            temp_info = await self.get_temp_info()
            if not temp_info:
                logger.warning("Could not get temperature info during cooling")
                await asyncio.sleep(10)
                continue
            
            # Check extruder temperature
            if not extruder_cooled:
                extruder_temp = temp_info.get_extruder_temp()
                if extruder_temp:
                    current_extruder_temp = extruder_temp.get_current()
                    if current_extruder_temp <= target_temp:
                        extruder_cooled = True
                        logger.info(f"Extruder cooled to {current_extruder_temp}°C")
            
            # Check bed temperature
            if not bed_cooled:
                bed_temp = temp_info.get_bed_temp()
                if bed_temp:
                    current_bed_temp = bed_temp.get_current()
                    if current_bed_temp <= target_temp:
                        bed_cooled = True
                        logger.info(f"Bed cooled to {current_bed_temp}°C")
            
            # Check if both have cooled
            if extruder_cooled and bed_cooled:
                logger.info("All components have cooled to target temperature")
                return True
            
            # Wait before next check
            await asyncio.sleep(10)  # Check every 10 seconds
        
        # Timeout reached
        logger.warning(f"Timeout after {timeout_seconds} seconds waiting for cooling")
        logger.warning(f"Extruder cooled: {extruder_cooled}, Bed cooled: {bed_cooled}")
        return False
