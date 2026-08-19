"""
FlashForge Python API - Control Module
"""

import logging
from typing import TYPE_CHECKING, Any

from ...models.responses import FilamentArgs
from ..constants.commands import Commands
from ..constants.endpoints import Endpoints
from ..network.utils import NetworkUtils, json_from_response
from .creator5_palette import snap_to_creator5_palette

if TYPE_CHECKING:
    from ...client import FlashForgeClient
    from ...tcp.ff_client import FlashForgeClient as TcpClient

logger = logging.getLogger(__name__)


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
        self._tcp_client: TcpClient | None = None

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
            True if the command is successful, False otherwise (including when the
            printer has no TCP control channel, e.g. Creator 5).
        """
        if not self.client.can_use_tcp("home_axes"):
            return False
        return await self.tcp_client.home_axes()

    async def home_axes_rapid(self) -> bool:
        """
        Performs a rapid homing of the X, Y, and Z axes.

        Returns:
            True if the command is successful, False otherwise (including when the
            printer has no TCP control channel, e.g. Creator 5).
        """
        if not self.client.can_use_tcp("home_axes_rapid"):
            return False
        return await self.tcp_client.rapid_home()

    async def set_external_filtration_on(self) -> bool:
        """
        Turns on the external filtration system.
        Requires the printer to have filtration control.

        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.filtration_control:
            return await self._send_filtration_command(
                FilamentArgs(internal="close", external="open")
            )
        logger.warning("set_external_filtration_on: filtration is not equipped on this printer.")
        return False

    async def set_internal_filtration_on(self) -> bool:
        """
        Turns on the internal filtration system.
        Requires the printer to have filtration control.

        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.filtration_control:
            return await self._send_filtration_command(
                FilamentArgs(internal="open", external="close")
            )
        logger.warning("set_internal_filtration_on: filtration is not equipped on this printer.")
        return False

    async def set_filtration_off(self) -> bool:
        """
        Turns off both internal and external filtration systems.
        Requires the printer to have filtration control.

        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.filtration_control:
            return await self._send_filtration_command(
                FilamentArgs(internal="close", external="close")
            )
        logger.warning("set_filtration_off: filtration is not equipped on this printer.")
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

        Returns:
            True if the command is successful, False otherwise.
        """
        if not self.client.led_control:
            logger.warning("set_led_on: LED control is not equipped on this printer.")
            return False
        return await self.send_control_command(Commands.LIGHT_CONTROL_CMD, {"status": "open"})

    async def set_led_off(self) -> bool:
        """
        Turns off the printer's LED lights.

        Returns:
            True if the command is successful, False otherwise.
        """
        if not self.client.led_control:
            logger.warning("set_led_off: LED control is not equipped on this printer.")
            return False
        return await self.send_control_command(Commands.LIGHT_CONTROL_CMD, {"status": "close"})

    async def turn_runout_sensor_on(self) -> bool:
        """
        Turns on the filament runout sensor.

        Returns:
            True if the command is successful, False otherwise (including when the
            printer has no TCP control channel, e.g. Creator 5).
        """
        if not self.client.can_use_tcp("turn_runout_sensor_on"):
            return False
        return await self.tcp_client.turn_runout_sensor_on()

    async def turn_runout_sensor_off(self) -> bool:
        """
        Turns off the filament runout sensor.

        Returns:
            True if the command is successful, False otherwise (including when the
            printer has no TCP control channel, e.g. Creator 5).
        """
        if not self.client.can_use_tcp("turn_runout_sensor_off"):
            return False
        return await self.tcp_client.turn_runout_sensor_off()

    async def configure_slot(self, slot: int, material_name: str, hex_rgb: str) -> bool:
        """
        Configures the material name and color metadata for a material-station slot.
        This information is shown on the printer UI and used for print validation; it
        does not move any filament. Available on the AD5X and the Creator 5 / Creator 5 Pro.

        The ``msConfig_cmd`` handler is confirmed present on the Creator 5
        (verified in firmware 1.9.2). The Creator 5 has no removable IFS; it
        surfaces its 4 tool heads as the 4 "slots", so this sets per-tool material
        metadata. Both models share the same ``OrcaServer`` command path and wire
        format. Note that **filament load/unload (``slotAction`` / ``ms_cmd``)
        remains AD5X-only** — the Creator 5 firmware has no ``ms_cmd``.

        The firmware accepts arbitrary material strings, but the two models render
        the slot color icon differently:

         - AD5X: accepts freeform hex (the leading "#" is stripped before sending).
         - Creator 5 / 5 Pro: renders an icon ONLY when ``rgb`` is a byte-for-byte,
           case-sensitive match against the firmware's 24-entry palette (WITH the
           "#"); any other value falls back to White. This method snaps the
           caller's color to the nearest palette entry automatically for the Creator 5.

        Args:
            slot: The slot number (1-4).
            material_name: The material type (e.g., "PLA", "PETG").
            hex_rgb: The color as a hex string.

        Returns:
            True if the command is successful, False otherwise.
        """
        if not self.client.is_ad5x and not self.client.is_creator5:
            logger.warning(
                "configure_slot: the material station is only available on the AD5X / Creator 5."
            )
            return False
        # The AD5X and Creator 5 use MUTUALLY EXCLUSIVE color wire formats (see
        # creator5_palette for the firmware match rules), so model-gate here:
        #  - AD5X: freeform hex, the leading "#" stripped ("RRGGBB"). Unchanged.
        #  - Creator 5 / 5 Pro: the firmware renders an icon ONLY on a byte-for-byte
        #    match against its 24-entry palette (case-sensitive, WITH the "#"). Snap
        #    the caller's color to the nearest palette entry in uppercase "#RRGGBB".
        if self.client.is_creator5:
            rgb = snap_to_creator5_palette(hex_rgb).hex
        else:
            rgb = hex_rgb[1:] if hex_rgb.startswith("#") else hex_rgb
        return await self.send_control_command(
            Commands.MATERIAL_STATION_CONFIG_CMD,
            {"slot": slot, "mt": material_name, "rgb": rgb},
        )

    async def send_control_command(self, command: str, args: dict[str, Any]) -> bool:
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
            "payload": {"cmd": command, "args": args},
        }

        # Log the command, never `payload`: it carries the serial number and
        # check code, and these lines end up pasted into bug reports.
        logger.debug("Sending control command %s with args %s", command, args)

        try:
            await self.client.is_http_client_busy()

            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.CONTROL),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                data = await json_from_response(response)
                logger.debug("Control command %s reply: %s", command, data)

                return NetworkUtils.is_ok(data)

        except Exception as e:
            logger.warning("Error in send_control_command (%s): %s", command, e)
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
            "action": command,
        }

        return await self.send_control_command(Commands.JOB_CONTROL_CMD, payload)

    async def _send_printer_control_cmd(
        self,
        z_offset: float = 0.0,
        print_speed: int = 100,
        chamber_fan_speed: int = 100,
        cooling_fan_speed: int = 100,
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
            "coolingLeftFan": 0,  # This is unused
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
        return await self.send_control_command(Commands.CIRCULATION_CONTROL_CMD, args.model_dump())

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
