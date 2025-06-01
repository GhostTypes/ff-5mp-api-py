"""
FlashForge Python API - Temperature Control Module
"""
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...client import FlashForgeClient
    from ...tcp.ff_client import FlashForgeClient as TcpClient


class TempControl:
    """
    Provides methods for controlling the temperatures of various printer components,
    including extruders and the print bed.
    """

    def __init__(self, client: "FlashForgeClient"):
        """
        Creates an instance of the TempControl class.
        
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

    async def set_extruder_temp(self, temperature: int, wait_for: bool = False) -> bool:
        """
        Sets the target temperature for an extruder.
        
        Args:
            temperature: The target temperature in Celsius.
            wait_for: Whether to wait for the heating operation to complete
            
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.set_extruder_temp(temperature, wait_for)

    async def set_bed_temp(self, temperature: int, wait_for: bool = False) -> bool:
        """
        Sets the target temperature for the print bed.
        
        Args:
            temperature: The target bed temperature in Celsius.
            wait_for: Whether to wait for the heating operation to complete
            
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.set_bed_temp(temperature, wait_for)

    async def cancel_extruder_temp(self) -> bool:
        """
        Cancels the heating of an extruder (sets target temperature to 0).

        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.cancel_extruder_temp()

    async def cancel_bed_temp(self) -> bool:
        """
        Cancels the heating of the print bed (sets target temperature to 0).
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.tcp_client.cancel_bed_temp()

    async def wait_for_part_cool(self, target_temp: float = 50.0, timeout_seconds: int = 1800) -> bool:
        """
        Waits for printer components to cool down to a safe temperature.
        
        Args:
            target_temp: The target temperature to wait for (default: 50°C).
            timeout_seconds: Maximum time to wait in seconds (default: 30 minutes).
            
        Returns:
            True if components cooled to target temperature, False if timeout or error.
        """
        return await self.tcp_client.wait_for_part_cool(target_temp, timeout_seconds)
