"""
FlashForge Python API - Temperature Control Module

Sets and cancels extruder/bed/chamber temperatures. The 5M / 5M Pro / AD5X use
direct TCP G-code/M-code commands; HTTP-only printers (Creator 5 / 5 Pro, no TCP
channel) use the HTTP ``temperatureCtl_cmd`` instead.
"""

import logging
from typing import TYPE_CHECKING

from ..constants.commands import Commands

if TYPE_CHECKING:
    from ...client import FlashForgeClient
    from ...tcp.ff_client import FlashForgeClient as TcpClient

logger = logging.getLogger(__name__)


# Sentinel value for `temperatureCtl_cmd` meaning "leave this heater unchanged"
# (partial update). Sending a real 0 / -100 would turn the heater off.
TEMP_NO_CHANGE = -200
# `temperatureCtl_cmd` value that turns a SCALAR heater (platform / chamber /
# rightNozzle) off.
TEMP_OFF = -100
# Value that turns a tool/nozzle OFF inside the `nozzles` array. Unlike the scalar
# heater fields (which accept TEMP_OFF = -100), the Creator 5 firmware's
# per-nozzle parser only treats a literal 0 as "off" — it ignores -100 in the
# `nozzles` array and the tool keeps heating (observed on live hardware;
# this is the v1.6.1 nozzle-off bugfix).
NOZZLE_OFF = 0
# Number of tool/nozzle entries the Creator 5 firmware requires in the
# `nozzles` array. The firmware ignores the array unless its length is exactly
# this (verified in the firmware).
NOZZLE_COUNT = 4


class TempControl:
    """
    Provides methods for controlling the temperatures of various printer components,
    including extruders and the print bed.

    Dual-API printers (5M / 5M Pro / AD5X) use TCP G-code commands; HTTP-only
    printers (Creator 5 / 5 Pro) route through the HTTP ``temperatureCtl_cmd``.
    """

    def __init__(self, client: "FlashForgeClient"):
        """
        Creates an instance of the TempControl class.

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

    async def _send_http_temp_command(
        self,
        right_nozzle: int | None = None,
        left_nozzle: int | None = None,
        platform: int | None = None,
        chamber: int | None = None,
        nozzles: list[int] | None = None,
    ) -> bool:
        """
        Sends a ``temperatureCtl_cmd`` over HTTP with the given setpoints.
        Unspecified heaters are left unchanged via the :data:`TEMP_NO_CHANGE`
        sentinel.

        The ``nozzles`` array is Creator 5-only (its 4-nozzle tool changer). The
        confirmed C5 payload ALWAYS carries a 4-entry array, even on a bed- or
        chamber-only command, so always include it on the C5 — defaulting
        unspecified tools to :data:`TEMP_NO_CHANGE` so a bed/chamber adjustment
        leaves the tools untouched.

        Returns:
            True if the command is acknowledged, False otherwise.
        """
        payload: dict[str, int | list[int]] = {
            "rightNozzle": right_nozzle if right_nozzle is not None else TEMP_NO_CHANGE,
            "leftNozzle": left_nozzle if left_nozzle is not None else TEMP_NO_CHANGE,
            "platform": platform if platform is not None else TEMP_NO_CHANGE,
            "chamber": chamber if chamber is not None else TEMP_NO_CHANGE,
        }
        # The `nozzles` array is Creator 5-only. The confirmed C5 payload always
        # carries a 4-entry array, even on a bed- or chamber-only command, so
        # always include it on the C5 — defaulting unspecified tools to
        # TEMP_NO_CHANGE so a bed/chamber adjustment leaves the tools untouched.
        if nozzles is not None:
            payload["nozzles"] = nozzles
        elif self.client.is_creator5:
            payload["nozzles"] = [TEMP_NO_CHANGE] * NOZZLE_COUNT
        return await self.client.control.send_control_command(Commands.TEMP_CONTROL_CMD, payload)

    def _build_nozzle_array(self, tool_index: int, value: int) -> list[int] | None:
        """
        Builds a :data:`NOZZLE_COUNT`-length ``nozzles`` array of
        :data:`TEMP_NO_CHANGE` placeholders with a single tool set to ``value``.

        Returns:
            The array, or None if ``tool_index`` is out of range.
        """
        if not isinstance(tool_index, int) or tool_index < 0 or tool_index >= NOZZLE_COUNT:
            logger.warning(
                "TempControl: tool_index %s out of range (0-%s).", tool_index, NOZZLE_COUNT - 1
            )
            return None
        nozzles = [TEMP_NO_CHANGE] * NOZZLE_COUNT
        nozzles[tool_index] = value
        return nozzles

    async def set_tool_temp(self, tool_index: int, temp: int) -> bool:
        """
        Sets the target temperature for a single tool/nozzle on a Creator 5 series
        tool-changer, leaving the other tools unchanged. Sent as a ``nozzles``
        array (Creator 5 / 5 Pro, HTTP-only).

        Args:
            tool_index: Zero-based tool index (0-3 for T0-T3).
            temp: Target temperature in Celsius.

        Returns:
            True if the command is acknowledged, False otherwise.
        """
        nozzles = self._build_nozzle_array(tool_index, temp)
        if nozzles is None:
            return False
        return await self._send_http_temp_command(nozzles=nozzles)

    async def set_tool_temps(self, temps: list[int]) -> bool:
        """
        Sets the target temperatures for all tools/nozzles on a Creator 5 series
        tool-changer in one command. Use :data:`TEMP_NO_CHANGE` (-200) to leave a
        tool unchanged or :data:`NOZZLE_OFF` (0) to turn one off (the firmware
        ignores the -100 sentinel inside the ``nozzles`` array). Must contain
        exactly :data:`NOZZLE_COUNT` entries.

        Args:
            temps: Per-tool target temperatures, ordered T0..T3.

        Returns:
            True if the command is acknowledged, False otherwise.
        """
        if len(temps) != NOZZLE_COUNT:
            logger.warning("set_tool_temps: expected %s temps, got %s.", NOZZLE_COUNT, len(temps))
            return False
        return await self._send_http_temp_command(nozzles=list(temps))

    async def cancel_tool_temp(self, tool_index: int) -> bool:
        """
        Cancels heating for a single tool/nozzle on a Creator 5 series tool-changer
        (sets its target to 0 via :data:`NOZZLE_OFF`), leaving the other tools
        unchanged.

        Args:
            tool_index: Zero-based tool index (0-3 for T0-T3).

        Returns:
            True if the command is acknowledged, False otherwise.
        """
        nozzles = self._build_nozzle_array(tool_index, NOZZLE_OFF)
        if nozzles is None:
            return False
        return await self._send_http_temp_command(nozzles=nozzles)

    async def set_extruder_temp(self, temperature: int, wait_for: bool = False) -> bool:
        """
        Sets the target temperature for the printer's extruder.

        On HTTP-only printers this routes to ``temperatureCtl_cmd``: the Creator 5
        drives its tools only via the ``nozzles`` array (targeting T0), while a
        forced-http_only AD5X / 5M keeps the ``rightNozzle`` scalar.

        Args:
            temperature: The target temperature in Celsius.
            wait_for: Whether to wait for the heating operation to complete (TCP only).

        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.http_only:
            # Creator 5 tools are driven ONLY via the `nozzles` array — the
            # firmware's temperature-control handler never reads
            # rightNozzle/leftNozzle. Target the primary tool (T0): the active
            # tool isn't reliably known over HTTP, so callers that need a
            # specific tool should use set_tool_temp(index, temp).
            if self.client.is_creator5:
                nozzles = self._build_nozzle_array(0, temperature)
                if nozzles is None:
                    return False
                return await self._send_http_temp_command(nozzles=nozzles)
            # Single-tool AD5X / 5M only reachable here if forced into http_only
            # mode; they keep the rightNozzle field (unchanged).
            return await self._send_http_temp_command(right_nozzle=temperature)
        return await self.tcp_client.set_extruder_temp(temperature, wait_for)

    async def set_bed_temp(self, temperature: int, wait_for: bool = False) -> bool:
        """
        Sets the target temperature for the printer's print bed.

        Args:
            temperature: The target bed temperature in Celsius.
            wait_for: Whether to wait for the heating operation to complete (TCP only).

        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.http_only:
            return await self._send_http_temp_command(platform=temperature)
        return await self.tcp_client.set_bed_temp(temperature, wait_for)

    async def cancel_extruder_temp(self) -> bool:
        """
        Cancels any ongoing extruder heating and sets its target temperature to 0.

        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.http_only:
            # See set_extruder_temp: Creator 5 tools are driven only via
            # `nozzles`. Turn the primary tool (T0) off (target 0, not the -100
            # sentinel the nozzles array ignores) while leaving the other tools
            # unchanged.
            if self.client.is_creator5:
                nozzles = self._build_nozzle_array(0, NOZZLE_OFF)
                if nozzles is None:
                    return False
                return await self._send_http_temp_command(nozzles=nozzles)
            # Single-tool AD5X / 5M (forced http_only) keep rightNozzle (unchanged).
            return await self._send_http_temp_command(right_nozzle=TEMP_OFF)
        return await self.tcp_client.cancel_extruder_temp()

    async def cancel_bed_temp(self) -> bool:
        """
        Cancels any ongoing print bed heating and sets its target temperature to 0.

        Returns:
            True if the command is successful, False otherwise.
        """
        if self.client.http_only:
            return await self._send_http_temp_command(platform=TEMP_OFF)
        return await self.tcp_client.cancel_bed_temp()

    async def set_chamber_temp(self, temp: int) -> bool:
        """
        Sets the target temperature for the printer's heated chamber. Only the
        Creator 5 series has a chamber heater, and those printers are HTTP-only,
        so this always goes over the HTTP ``temperatureCtl_cmd``. The firmware
        caps the chamber at 80°C.

        Args:
            temp: The target temperature in Celsius.

        Returns:
            True if the command is acknowledged, False otherwise.
        """
        if not self.client.is_creator5 and not self.client.is_creator5_pro:
            logger.warning(
                "set_chamber_temp: the chamber heater is only available on the Creator 5 series."
            )
            return False
        return await self._send_http_temp_command(chamber=temp)

    async def cancel_chamber_temp(self) -> bool:
        """
        Cancels any ongoing chamber heating and sets its target temperature to 0.

        Returns:
            True if the command is acknowledged, False otherwise.
        """
        if not self.client.is_creator5 and not self.client.is_creator5_pro:
            logger.warning(
                "cancel_chamber_temp: the chamber heater is only available on the Creator 5 series."
            )
            return False
        return await self._send_http_temp_command(chamber=TEMP_OFF)

    async def wait_for_part_cool(
        self, target_temp: float = 50.0, timeout_seconds: int = 1800
    ) -> bool:
        """
        Waits for printer components to cool down to a safe temperature.

        Relies on TCP G-code polling and is therefore unavailable on HTTP-only
        printers (Creator 5 / 5 Pro); callers should poll ``info.get()`` instead.

        Args:
            target_temp: The target temperature to wait for (default: 50°C).
            timeout_seconds: Maximum time to wait in seconds (default: 30 minutes).

        Returns:
            True if components cooled to target temperature, False if timeout, error,
            or HTTP-only (no TCP polling channel).
        """
        if self.client.http_only:
            logger.warning(
                "wait_for_part_cool is unavailable over an HTTP-only connection; "
                "poll info.get() instead."
            )
            return False
        return await self.tcp_client.wait_for_part_cool(target_temp, timeout_seconds)
