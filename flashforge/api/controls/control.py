"""
FlashForge Python API - Control Module
"""
from typing import TYPE_CHECKING, Any, Dict, Optional

import aiohttp

from ...models.responses import FilamentArgs
from ..constants.commands import Commands
from ..constants.endpoints import Endpoints
from ..network.utils import NetworkUtils

if TYPE_CHECKING:
    from ...client import FlashForgeClient
    from ...tcp.ff_client import FlashForgeClient as TcpClient


class Control:
    """
    Provides methods for controlling various aspects of the FlashForge 3D printer.
    This includes homing axes, controlling filtration, camera, speed, Z-axis offset,
    fans, LEDs, and filament operations.
    """

    def __init__(self, client: "FlashForgeClient"):
        """
        Creates an instance of the Control class.
        
        Args:
            client: The FlashForgeClient instance used for communication with the printer.
        """
        self.client = client
        self._tcp_client: Optional[TcpClient] = None

    @property
    def tcp_client(self) -> "TcpClient":
        """Get the TCP client instance."""
        if self._tcp_client is None:
            self._tcp_client = self.client.tcp_client
        return self._tcp_client

    async def home_axes(self) -> bool:
        """
        Homes the X, Y, and Z axes of the printer.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.home_axes()

    async def home_axes_rapid(self) -> bool:
        """
        Performs a rapid homing of the X, Y, and Z axes.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.rapid_home()

    async def set_external_filtration_on(self) -> bool:
        """
        Turns on the external filtration system.
        Requires the printer to have filtration control.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.filtration_control:
            return await self._send_filtration_command(FilamentArgs(False, True))
        print("SetExternalFiltrationOn() error, filtration not equipped.")
        return False

    async def set_internal_filtration_on(self) -> bool:
        """
        Turns on the internal filtration system.
        Requires the printer to have filtration control.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.filtration_control:
            return await self._send_filtration_command(FilamentArgs(True, False))
        print("SetInternalFiltrationOn() error, filtration not equipped.")
        return False

    async def set_filtration_off(self) -> bool:
        """
        Turns off both internal and external filtration systems.
        Requires the printer to have filtration control.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.filtration_control:
            return await self._send_filtration_command(FilamentArgs(False, False))
        print("SetFiltrationOff() error, filtration not equipped.")
        return False

    async def turn_camera_on(self) -> bool:
        """
        Turns on the printer's camera.
        Only applicable for Pro models.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        if not self.client.is_pro:
            return False
        return await self._send_camera_command(True)

    async def turn_camera_off(self) -> bool:
        """
        Turns off the printer's camera.
        Only applicable for Pro models.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        if not self.client.is_pro:
            return False
        return await self._send_camera_command(False)

    async def set_speed_override(self, speed: int) -> bool:
        """
        Sets the print speed override.
        
        Args:
            speed: The desired print speed percentage (e.g., 100 for normal speed).
            
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self._send_printer_control_cmd(print_speed=speed)

    async def set_z_axis_override(self, offset: float) -> bool:
        """
        Sets the Z-axis offset override.
        
        Args:
            offset: The Z-axis offset value.
            
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self._send_printer_control_cmd(z_offset=offset)

    async def set_chamber_fan_speed(self, speed: int) -> bool:
        """
        Sets the chamber fan speed.
        
        Args:
            speed: The desired chamber fan speed percentage.
            
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self._send_printer_control_cmd(chamber_fan_speed=speed)

    async def set_cooling_fan_speed(self, speed: int) -> bool:
        """
        Sets the cooling fan speed.
        
        Args:
            speed: The desired cooling fan speed percentage.
            
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self._send_printer_control_cmd(cooling_fan_speed=speed)

    async def set_led_on(self) -> bool:
        """
        Turns on the printer's LED lights.
        Requires the printer to have LED control.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.led_control:
            return await self.send_control_command(Commands.LIGHT_CONTROL_CMD, {"status": "open"})
        print("SetLedOn() error, LEDs not equipped.")
        return False

    async def set_led_off(self) -> bool:
        """
        Turns off the printer's LED lights.
        Requires the printer to have LED control.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.led_control:
            return await self.send_control_command(Commands.LIGHT_CONTROL_CMD, {"status": "close"})
        print("SetLedOff() error, LEDs not equipped.")
        return False

    async def turn_runout_sensor_on(self) -> bool:
        """
        Turns on the filament runout sensor.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.turn_runout_sensor_on()

    async def turn_runout_sensor_off(self) -> bool:
        """
        Turns off the filament runout sensor.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.turn_runout_sensor_off()

    async def send_control_command(self, command: str, args: Dict[str, Any]) -> bool:
        """
        Sends a generic control command to the printer via HTTP POST.
        
        Args:
            command: The specific command string to send.
            args: The arguments or payload specific to the command.
            
        Returns:
            True if the command is acknowledged with a success code, False otherwise.
        """
        payload = {
            "serialNumber": self.client.serial_number,
            "checkCode": self.client.check_code,
            "payload": {
                "cmd": command,
                "args": args
            }
        }

        print(f"SendControlCommand:\n{payload}")

        try:
            await self.client.is_http_client_busy()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.client.get_endpoint(Endpoints.CONTROL),
                        json=payload,
                        headers={"Content-Type": "application/json"}
                ) as response:
                    # Fix for FlashForge printer's malformed Content-Type header
                    # Some printers return "appliation/json" instead of "application/json"
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        # Fallback: manually parse as JSON if Content-Type is malformed
                        text = await response.text()
                        import json
                        data = json.loads(text)

                    print(f"Command reply: {data}")

                    return NetworkUtils.is_ok(data)

        except Exception as e:
            print(f"Error in send_control_command: {e}")
            return False
        finally:
            self.client.release_http_client()

    async def send_job_control_cmd(self, command: str) -> bool:
        """
        Sends a job control command.
        
        Args:
            command: The job control command to send.
            
        Returns:
            True if the command is successful, False otherwise.
        """
        payload = {
            "jobID": "",  # jobID seems to be optional or not strictly enforced
            "action": command
        }

        return await self.send_control_command(Commands.JOB_CONTROL_CMD, payload)

    async def _send_printer_control_cmd(
            self,
            z_offset: float = 0.0,
            print_speed: int = 100,
            chamber_fan_speed: int = 100,
            cooling_fan_speed: int = 100
    ) -> bool:
        """
        Sends a command to control various printer settings during a print.
        
        Args:
            z_offset: The Z-axis compensation offset.
            print_speed: The print speed percentage.
            chamber_fan_speed: The chamber fan speed percentage.
            cooling_fan_speed: The cooling fan speed percentage.
            
        Returns:
            True if the command is successful, False otherwise.
        """
        info = await self.client.info.get()

        if info and info.current_print_layer < 2:
            # Don't accidentally turn on the fans in the initial layers
            chamber_fan_speed = 0
            cooling_fan_speed = 0

        if not self._is_printing(info):
            raise Exception("Attempted to send printerCtl_cmd with no active job")

        payload = {
            "zAxisCompensation": z_offset,
            "speed": print_speed,
            "chamberFan": chamber_fan_speed,
            "coolingFan": cooling_fan_speed,
            "coolingLeftFan": 0  # This is unused
        }

        return await self.send_control_command(Commands.PRINTER_CONTROL_CMD, payload)

    async def _send_filtration_command(self, args: FilamentArgs) -> bool:
        """
        Sends a command to control the printer's filtration system.
        
        Args:
            args: The filtration arguments specifying internal and external fan states.
            
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.send_control_command(Commands.CIRCULATION_CONTROL_CMD, args.dict())

    async def _send_camera_command(self, enabled: bool) -> bool:
        """
        Sends a command to control the printer's camera.
        
        Args:
            enabled: True to turn the camera on ("open"), false to turn it off ("close").
            
        Returns:
            True if the command is successful, False otherwise.
        """
        payload = {"action": "open" if enabled else "close"}
        return await self.send_control_command(Commands.CAMERA_CONTROL_CMD, payload)

    def _is_printing(self, info: Any) -> bool:
        """
        Checks if the printer is currently printing based on its status information.

        Args:
            info: The printer information object.

        Returns:
            True if the printer status is "printing", False otherwise.
        """
        return info and getattr(info, "status", "") == "printing"
