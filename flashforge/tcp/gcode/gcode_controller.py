"""
G-code controller for FlashForge 3D printers.

This module provides high-level G-code command methods that build upon
the basic TCP communication provided by FlashForgeTcpClient.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from .gcodes import GCodes

if TYPE_CHECKING:
    from ..ff_client import FlashForgeClient

logger = logging.getLogger(__name__)


class GCodeController:
    """
    Controller for sending specific G-code commands to FlashForge printers.
    
    This class provides convenient methods for common printer operations
    like LED control, job management, movement, and temperature control.
    """

    def __init__(self, client: 'FlashForgeClient') -> None:
        """
        Initialize the G-code controller.
        
        Args:
            client: The FlashForgeClient instance for sending commands
        """
        self.client = client

    async def led_on(self) -> bool:
        """
        Turn the printer's LED lights on.
        
        Returns:
            True if the command was successful, False otherwise
        """
        return await self.client.send_cmd_ok(GCodes.CMD_LED_ON)

    async def led_off(self) -> bool:
        """
        Turn the printer's LED lights off.
        
        Returns:
            True if the command was successful, False otherwise
        """
        return await self.client.send_cmd_ok(GCodes.CMD_LED_OFF)

    async def pause_job(self) -> bool:
        """
        Pause the current print job.
        
        Returns:
            True if the command was successful, False otherwise
        """
        return await self.client.send_cmd_ok(GCodes.CMD_PAUSE_PRINT)

    async def resume_job(self) -> bool:
        """
        Resume a paused print job.
        
        Returns:
            True if the command was successful, False otherwise
        """
        return await self.client.send_cmd_ok(GCodes.CMD_RESUME_PRINT)

    async def stop_job(self) -> bool:
        """
        Stop the current print job.
        
        Returns:
            True if the command was successful, False otherwise
        """
        return await self.client.send_cmd_ok(GCodes.CMD_STOP_PRINT)

    async def start_job(self, filename: str) -> bool:
        """
        Start a print job from a file stored on the printer.
        
        Args:
            filename: The name of the file to print (typically without path)
            
        Returns:
            True if the command was successful, False otherwise
        """
        cmd = GCodes.CMD_START_PRINT.replace("%%filename%%", filename)
        return await self.client.send_cmd_ok(cmd)

    async def home(self) -> bool:
        """
        Home all axes (X, Y, Z) of the printer.
        
        Returns:
            True if the command was successful, False otherwise
        """
        return await self.client.send_cmd_ok(GCodes.CMD_HOME_AXES)

    async def rapid_home(self) -> bool:
        """
        Perform a rapid homing of all axes.
        
        Note: This uses the same command as regular homing in the current implementation.
        
        Returns:
            True if the command was successful, False otherwise
        """
        # In the TypeScript implementation, this is the same as home()
        return await self.home()

    async def move(self, x: float, y: float, z: float, feedrate: int) -> bool:
        """
        Move the extruder to a specified X, Y, Z position.
        
        Args:
            x: The target X coordinate
            y: The target Y coordinate  
            z: The target Z coordinate
            feedrate: The feedrate for the movement in mm/min
            
        Returns:
            True if the command was successful, False otherwise
        """
        cmd = f"~G1 X{x} Y{y} Z{z} F{feedrate}"
        return await self.client.send_cmd_ok(cmd)

    async def move_extruder(self, x: float, y: float, feedrate: int) -> bool:
        """
        Move the extruder to a specified X, Y position.
        
        Args:
            x: The target X coordinate
            y: The target Y coordinate
            feedrate: The feedrate for the movement in mm/min
            
        Returns:
            True if the command was successful, False otherwise
        """
        cmd = f"~G1 X{x} Y{y} F{feedrate}"
        return await self.client.send_cmd_ok(cmd)

    async def extrude(self, length: float, feedrate: int = 450) -> bool:
        """
        Command the extruder to extrude a specific length of filament.
        
        Args:
            length: The length of filament to extrude in millimeters
            feedrate: The feedrate for extrusion in mm/min (default: 450)
            
        Returns:
            True if the command was successful, False otherwise
        """
        cmd = f"~G1 E{length} F{feedrate}"
        return await self.client.send_cmd_ok(cmd)

    async def set_extruder_temp(self, temp: int, wait_for: bool = False) -> bool:
        """
        Set the target temperature for the extruder.
        
        Args:
            temp: The target temperature in Celsius
            wait_for: If True, wait until the target temperature is reached
            
        Returns:
            True if the command was successful, False otherwise
        """
        if wait_for:
            cmd = f"{GCodes.WAIT_FOR_HOTEND_TEMP} S{temp}"
            ok = await self.client.send_cmd_ok(cmd)
            if not ok:
                return False
            # Wait for temperature to be reached
            return await self.wait_for_extruder_temp(temp)
        else:
            cmd = f"~M104 S{temp}"
            return await self.client.send_cmd_ok(cmd)

    async def set_bed_temp(self, temp: int, wait_for: bool = False) -> bool:
        """
        Set the target temperature for the print bed.
        
        Args:
            temp: The target temperature in Celsius  
            wait_for: If True, wait until the target temperature is reached
            
        Returns:
            True if the command was successful, False otherwise
        """
        if wait_for:
            cmd = f"{GCodes.WAIT_FOR_BED_TEMP} S{temp}"
            ok = await self.client.send_cmd_ok(cmd)
            if not ok:
                return False
            # Wait for temperature to be reached
            return await self.wait_for_bed_temp(temp)
        else:
            cmd = f"~M140 S{temp}"
            return await self.client.send_cmd_ok(cmd)

    async def cancel_extruder_temp(self) -> bool:
        """
        Cancel extruder heating and set its target temperature to 0.
        
        Returns:
            True if the command was successful, False otherwise
        """
        cmd = "~M104 S0"
        ok = await self.client.send_cmd_ok(cmd)
        return ok

    async def cancel_bed_temp(self, wait_for_cool: bool = False) -> bool:
        """
        Cancel print bed heating and set its target temperature to 0.
        
        Args:
            wait_for_cool: If True, wait for the bed to cool down after canceling
            
        Returns:
            True if the command was successful, False otherwise
        """
        cmd = "~M140 S0"
        ok = await self.client.send_cmd_ok(cmd)
        if not ok:
            return False

        if wait_for_cool:
            # Wait for bed to cool down to a reasonable temperature
            return await self.wait_for_bed_temp(40, cooling=True)

        return True

    async def wait_for_bed_temp(self, target_temp: int, cooling: bool = False, timeout: int = 600) -> bool:
        """
        Wait for the bed temperature to reach the target.
        
        Args:
            target_temp: The target temperature to wait for
            cooling: If True, wait for temperature to drop below target; otherwise wait to reach target
            timeout: Maximum time to wait in seconds (default: 600)
            
        Returns:
            True if target temperature was reached, False on timeout or error
        """
        start_time = asyncio.get_event_loop().time()
        timeout_time = start_time + timeout

        while asyncio.get_event_loop().time() < timeout_time:
            temp_info = await self.client.get_temp_info()
            if temp_info:
                bed_temp = temp_info.get_bed_temp()
                if bed_temp:
                    current_temp = bed_temp.get_current()
                    if cooling:
                        if current_temp <= target_temp:
                            return True
                    else:
                        if abs(current_temp - target_temp) <= 2:  # Within 2°C tolerance
                            return True

            await asyncio.sleep(5)  # Check every 5 seconds

        logger.warning(f"Timeout waiting for bed temperature {'cooling to' if cooling else 'heating to'} {target_temp}°C")
        return False

    async def wait_for_extruder_temp(self, target_temp: int, timeout: int = 600) -> bool:
        """
        Wait for the extruder temperature to reach the target.
        
        Args:
            target_temp: The target temperature to wait for
            timeout: Maximum time to wait in seconds (default: 600)
            
        Returns:
            True if target temperature was reached, False on timeout or error
        """
        start_time = asyncio.get_event_loop().time()
        timeout_time = start_time + timeout

        while asyncio.get_event_loop().time() < timeout_time:
            temp_info = await self.client.get_temp_info()
            if temp_info:
                extruder_temp = temp_info.get_extruder_temp()
                if extruder_temp:
                    current_temp = extruder_temp.get_current()
                    if abs(current_temp - target_temp) <= 2:  # Within 2°C tolerance
                        return True

            await asyncio.sleep(5)  # Check every 5 seconds

        logger.warning(f"Timeout waiting for extruder temperature to reach {target_temp}°C")
        return False
