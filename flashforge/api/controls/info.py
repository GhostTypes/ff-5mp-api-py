"""
FlashForge Python API - Info Module
"""

import logging
import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from ...exceptions import FlashForgeResponseError
from ...models.machine_info import FFMachineInfo, MachineState, Temperature
from ...models.responses import DetailResponse, FFPrinterDetail
from ..constants.endpoints import Endpoints
from ..misc.redaction import redact_model
from ..network.utils import json_from_response

if TYPE_CHECKING:
    from ...client import FlashForgeClient

logger = logging.getLogger(__name__)


# Firmware-reported PIDs from FlashForge's /detail endpoint. These are stable
# identifiers set by firmware, unlike the user-mutable `name` field.
PID_5M = 35
PID_5M_PRO = 36
PID_AD5X = 38
PID_CREATOR5 = 40
PID_CREATOR5_PRO = 41
KNOWN_HTTP_PIDS = {
    PID_5M,
    PID_5M_PRO,
    PID_AD5X,
    PID_CREATOR5,
    PID_CREATOR5_PRO,
}

# Immutable model display names keyed by firmware PID. Used as a fallback for
# `model` when the printer doesn't report the `model` field (older firmware).
PID_MODEL_NAMES: dict[int, str] = {
    PID_5M: "Adventurer 5M",
    PID_5M_PRO: "Adventurer 5M Pro",
    PID_AD5X: "AD5X",
    PID_CREATOR5: "Creator 5",
    PID_CREATOR5_PRO: "Creator 5 Pro",
}


class MachineInfoParser:
    """
    Transforms printer detail data from the API response format into a structured FFMachineInfo object.
    This class centralizes the logic for mapping and calculating various properties of the printer's state
    and capabilities based on the raw data received from the printer.
    """

    @staticmethod
    def from_detail(detail: FFPrinterDetail | None) -> FFMachineInfo | None:
        """
        Converts printer details from the API response format to our internal FFMachineInfo model.

        Args:
            detail: The FFPrinterDetail object received from the printer's API.

        Returns:
            An FFMachineInfo object containing structured and formatted printer information,
            or None if the input detail is None or an error occurs during processing.
        """
        if not detail:
            return None

        try:
            # Calculate derived values
            estimated_time = getattr(detail, "estimated_time", 0) or 0
            print_eta = MachineInfoParser._format_time_from_seconds(estimated_time)
            formatted_run_time = MachineInfoParser._format_time_from_seconds(
                getattr(detail, "print_duration", 0) or 0
            )
            completion_time = datetime.now() + timedelta(seconds=estimated_time)

            total_minutes = getattr(detail, "cumulative_print_time", 0) or 0
            hours = total_minutes // 60
            minutes = total_minutes % 60
            formatted_total_run_time = f"{hours}h:{minutes}m"

            # Boolean status conversions
            auto_shutdown = (getattr(detail, "auto_shutdown", "") or "") == "open"
            door_open = (getattr(detail, "door_status", "") or "") == "open"
            external_fan_on = (getattr(detail, "external_fan_status", "") or "") == "open"
            internal_fan_on = (getattr(detail, "internal_fan_status", "") or "") == "open"
            lights_on = (getattr(detail, "light_status", "") or "") == "open"

            # Calculate filament estimates
            total_job_filament_meters = (getattr(detail, "estimated_right_len", 0) or 0) / 1000.0
            print_progress = getattr(detail, "print_progress", 0) or 0
            est_length = total_job_filament_meters * print_progress
            est_weight = (getattr(detail, "estimated_right_weight", 0) or 0) * print_progress
            # Material Station presence, derived rather than read off a single
            # field. `hasMatlStation` is AD5X-only: the Creator 5 series omits it
            # from /detail entirely (verified on a Creator 5 Pro, pid 41, firmware
            # 1.9.4) while reporting a fully populated matlStationInfo with four
            # loaded slots, so an absent flag means "not reported", never "absent
            # hardware". Populated slot data is the reliable signal.
            has_material_station = (
                getattr(detail, "has_matl_station", None) is True
                or (getattr(getattr(detail, "matl_station_info", None), "slot_cnt", 0) or 0) > 0
                or len(getattr(getattr(detail, "matl_station_info", None), "slot_infos", []) or [])
                > 0
            )
            printer_name = getattr(detail, "name", "") or ""
            pid = getattr(detail, "pid", None)
            detail_model = getattr(detail, "model", None) or ""

            if pid in KNOWN_HTTP_PIDS:
                is_ad5x = pid == PID_AD5X
                is_pro = pid == PID_5M_PRO
                is_creator5 = pid in (PID_CREATOR5, PID_CREATOR5_PRO)
                is_creator5_pro = pid == PID_CREATOR5_PRO
            else:
                # Fallback for firmware that doesn't report pid: legacy
                # name+capability heuristic. Vulnerable to user renames, which
                # is why pid-based detection is preferred when available.
                #
                # IMPORTANT: detect the Creator 5 family *first*. A user-set
                # name like "Creator 5 Pro" contains "Pro", so a naive
                # `"Pro" in name` check would mis-classify it as a 5M Pro.
                is_creator5 = "Creator 5" in printer_name
                is_creator5_pro = is_creator5 and bool(
                    re.search(r"Creator 5 Pro", detail_model or printer_name, re.IGNORECASE)
                )
                is_ad5x = (
                    printer_name.upper() == "AD5X" or has_material_station
                ) and not is_creator5
                is_pro = "Pro" in printer_name and not is_ad5x and not is_creator5

            # Per-tool temperatures. Creator 5 series report nozzleTemps[] /
            # nozzleTargetTemps[]; single-nozzle models don't, so fall back to a
            # 1-element array mirroring the right/main extruder.
            nozzle_temps = getattr(detail, "nozzle_temps", None)
            nozzle_target_temps = getattr(detail, "nozzle_target_temps", None)
            if nozzle_temps:
                tool_temps = [
                    Temperature(
                        current=t or 0.0,
                        set=(
                            nozzle_target_temps[i]
                            if nozzle_target_temps and i < len(nozzle_target_temps)
                            else 0.0
                        )
                        or 0.0,
                    )
                    for i, t in enumerate(nozzle_temps)
                ]
            else:
                tool_temps = [
                    Temperature(
                        current=getattr(detail, "right_temp", 0) or 0.0,
                        set=getattr(detail, "right_target_temp", 0) or 0.0,
                    )
                ]

            # Capability flags. Derived from presence/value, never assumed from
            # the model family alone. Only the Creator 5 Pro has a confirmed
            # door sensor; on every other model `doorStatus` is cosmetic.
            has_camera = getattr(detail, "camera", None) == 1 or bool(
                getattr(detail, "camera_stream_url", "") or ""
            )
            has_lidar = getattr(detail, "lidar", None) == 1
            has_door_sensor = is_creator5_pro
            # Not every Creator 5 has the heated chamber. FFPrinterDetail maps
            # the firmware's "no sensor" sentinel (-108) to None, so an absent
            # reading is the signal - never the model family, which is what left
            # chamber-less units with three entities pinned at 0 C.
            chamber_temp_value = getattr(detail, "chamber_temp", None)
            has_chamber_sensor = chamber_temp_value is not None

            # Immutable model name resolution: prefer the firmware `model`
            # field, then a PID-derived name, then the user-set name.
            pid_model_name = PID_MODEL_NAMES.get(pid) if pid is not None else None
            model_value = detail_model or pid_model_name or printer_name or ""

            # Prefer the firmware-reported nozzle count; fall back to the parsed
            # per-tool array length so single-nozzle models still report 1.
            nozzle_count = getattr(detail, "nozzle_cnt", None) or len(tool_temps)

            # Build the FFMachineInfo object
            machine_info = FFMachineInfo(
                # Auto-shutdown settings
                auto_shutdown=auto_shutdown,
                auto_shutdown_time=getattr(detail, "auto_shutdown_time", 0) or 0,
                # Camera
                camera_stream_url=getattr(detail, "camera_stream_url", "") or "",
                # Fan speeds
                chamber_fan_speed=getattr(detail, "chamber_fan_speed", 0) or 0,
                cooling_fan_speed=getattr(detail, "cooling_fan_speed", 0) or 0,
                cooling_fan_left_speed=getattr(detail, "cooling_fan_left_speed", None),
                # Cumulative stats
                cumulative_filament=getattr(detail, "cumulative_filament", 0) or 0,
                cumulative_print_time=getattr(detail, "cumulative_print_time", 0) or 0,
                # Current print speed
                current_print_speed=getattr(detail, "current_print_speed", 0) or 0,
                # Disk space
                free_disk_space=f"{(getattr(detail, 'remaining_disk_space', 0) or 0):.2f}",
                # Door and error status
                door_open=door_open,
                error_code=getattr(detail, "error_code", "") or "",
                # Current print estimates
                est_length=est_length,
                est_weight=est_weight,
                estimated_time=getattr(detail, "estimated_time", 0) or 0,
                # Fans & LED status
                external_fan_on=external_fan_on,
                internal_fan_on=internal_fan_on,
                lights_on=lights_on,
                # Network
                ip_address=getattr(detail, "ip_addr", "") or "",
                mac_address=getattr(detail, "mac_addr", "") or "",
                # Print settings
                fill_amount=getattr(detail, "fill_amount", 0) or 0,
                firmware_version=getattr(detail, "firmware_version", "") or "",
                name=printer_name,
                pid=pid,
                is_pro=is_pro,
                is_ad5x=is_ad5x,
                is_creator5=is_creator5,
                is_creator5_pro=is_creator5_pro,
                model=model_value,
                nozzle_size=getattr(detail, "nozzle_model", "") or "",
                nozzle_count=nozzle_count,
                # Temperatures
                print_bed=Temperature(
                    current=getattr(detail, "plat_temp", 0) or 0,
                    set=getattr(detail, "plat_target_temp", 0) or 0,
                ),
                extruder=Temperature(
                    current=getattr(detail, "right_temp", 0) or 0,
                    set=getattr(detail, "right_target_temp", 0) or 0,
                ),
                chamber=Temperature(
                    current=getattr(detail, "chamber_temp", 0) or 0,
                    set=getattr(detail, "chamber_target_temp", 0) or 0,
                ),
                tool_temps=tool_temps,
                # Capability flags (presence-derived)
                has_camera=has_camera,
                has_lidar=has_lidar,
                has_door_sensor=has_door_sensor,
                has_chamber_sensor=has_chamber_sensor,
                # Current print stats
                print_duration=getattr(detail, "print_duration", 0) or 0,
                print_file_name=getattr(detail, "print_file_name", "") or "",
                print_file_thumb_url=getattr(detail, "print_file_thumb_url", "") or "",
                current_print_layer=getattr(detail, "print_layer", 0) or 0,
                print_progress=print_progress,
                print_progress_int=int(print_progress * 100),
                print_speed_adjust=getattr(detail, "print_speed_adjust", 0) or 0,
                filament_type=getattr(detail, "right_filament_type", "") or "",
                # Machine state
                machine_state=MachineInfoParser._get_machine_state(
                    getattr(detail, "status", "") or ""
                ),
                status=getattr(detail, "status", "") or "",
                total_print_layers=getattr(detail, "target_print_layer", 0) or 0,
                tvoc=getattr(detail, "tvoc", 0) or 0,
                z_axis_compensation=getattr(detail, "z_axis_compensation", 0) or 0,
                # Cloud codes
                flash_cloud_register_code=getattr(detail, "flash_register_code", "") or "",
                polar_cloud_register_code=getattr(detail, "polar_register_code", "") or "",
                # Extras
                print_eta=print_eta,
                completion_time=completion_time,
                formatted_run_time=formatted_run_time,
                formatted_total_run_time=formatted_total_run_time,
                # Material Station (AD5X / Creator 5 series)
                has_matl_station=has_material_station,
                matl_station_info=getattr(detail, "matl_station_info", None),
                indep_matl_info=getattr(detail, "indep_matl_info", None),
            )

            return machine_info

        except Exception as error:
            logger.warning(
                "Could not parse the /detail payload into FFMachineInfo; the caller sees "
                "this as an unreachable printer. %s",
                error,
            )
            # Redacted: this dump carries the MAC, IP and cloud registration
            # codes, and it exists to be pasted into a bug report.
            logger.debug("Detail object that failed to parse: %s", redact_model(detail))
            return None

    @staticmethod
    def _format_time_from_seconds(seconds: float) -> str:
        """Format a duration in seconds as HH:MM."""
        try:
            valid_seconds = int(seconds) if isinstance(seconds, (int, float)) else 0
            hours = valid_seconds // 3600
            minutes = (valid_seconds % 3600) // 60
            return f"{hours:02d}:{minutes:02d}"
        except Exception:
            return "00:00"

    @staticmethod
    def _get_machine_state(status: str) -> MachineState:
        """Map raw status strings into the public machine state enum.

        An unmapped value costs the consumer everything the field is for: it
        becomes ``UNKNOWN``, which in Home Assistant renders as "unknown" - the
        one state that says nothing, at the moment the user most needs to know
        what the printer is doing. Both additions below were found that way, in
        a log full of `Unknown machine status received` while a Creator 5 Pro sat
        paused on a detected clog.

        Consumers may map this enum onto a fixed set of values - the Home
        Assistant integration's Machine Status sensor is a `device_class=ENUM`
        with an explicit `options` list - so a *new* member is a breaking change
        for them, while mapping onto an existing one is not. Prefer the closest
        existing state unless a new one is worth coordinating.
        """
        valid_status = status.lower() if isinstance(status, str) else ""
        state_mapping = {
            "ready": MachineState.READY,
            "busy": MachineState.BUSY,
            "calibrate_doing": MachineState.CALIBRATING,
            "error": MachineState.ERROR,
            "heating": MachineState.HEATING,
            "printing": MachineState.PRINTING,
            "pausing": MachineState.PAUSING,
            # The Creator 5 Pro reports "pause" for a print that is paused,
            # where the documented value is "paused" - both are mapped, because
            # firmware that reports one is not a reason to drop the other.
            # Observed on pid 41, firmware 1.9.4, whenever the printer paused
            # itself on a detected clog.
            "pause": MachineState.PAUSED,
            "paused": MachineState.PAUSED,
            "cancel": MachineState.CANCELLED,
            "completed": MachineState.COMPLETED,
            # Reported while a file is being transferred to the printer. Not a
            # print, but not idle either, so BUSY is the honest existing fit; a
            # dedicated state would need consumers to add it to their option
            # lists first.
            "downloading": MachineState.BUSY,
        }

        if valid_status in state_mapping:
            return state_mapping[valid_status]

        if valid_status:
            logger.warning("Unknown machine status received: %r", status)
        return MachineState.UNKNOWN


class Info:
    """
    Provides methods for retrieving various information and status details from the FlashForge 3D printer.
    This includes general machine information, printing status, and raw detail responses.
    """

    def __init__(self, client: "FlashForgeClient"):
        """
        Creates an instance of the Info class.

        Args:
            client: The FlashForgeClient instance used for communication with the printer.
        """
        self.client = client

    async def get(self) -> FFMachineInfo | None:
        """
        Retrieves comprehensive machine information, processed into the FFMachineInfo model.
        This method fetches detailed data from the printer and transforms it.

        Returns:
            An FFMachineInfo object, or None if the printer could not be reached.

        Raises:
            FlashForgeResponseError: The printer answered but the payload could
                not be understood. Distinct from a None return, which means the
                request never got through.
        """
        detail_response = await self.get_detail_response()
        if detail_response is None or detail_response.detail is None:
            return None

        machine_info = MachineInfoParser.from_detail(detail_response.detail)
        if machine_info is None:
            # We validated the payload but could not build our own model from
            # it - that is a bug on our side, not an unreachable printer, and
            # reporting it as the latter is what issue #18 was about.
            raise FlashForgeResponseError(
                "The /detail payload was read but could not be converted into machine info",
                endpoint=Endpoints.DETAIL,
            )
        return machine_info

    async def is_printing(self) -> bool:
        """
        Checks if the printer is currently in the "printing" state.

        These three convenience wrappers keep their documented "return the
        fallback on any failure" contract, so a caller polling for a boolean is
        not forced to handle an exception. The failure is still logged, and
        callers that need to distinguish causes should use `get()` directly.

        Returns:
            True if the printer is printing, False otherwise or if status cannot be determined.
        """
        info = await self._get_or_none()
        return info.status == "printing" if info else False

    async def get_status(self) -> str | None:
        """
        Retrieves the raw status string of the printer (e.g., "ready", "printing", "error").

        Returns:
            The status string, or None if it cannot be determined.
        """
        info = await self._get_or_none()
        return info.status if info else None

    async def get_machine_state(self) -> MachineState | None:
        """
        Retrieves the machine state as a MachineState enum value.

        Returns:
            A MachineState enum value, or None if it cannot be determined.
        """
        info = await self._get_or_none()
        return info.machine_state if info else None

    async def _get_or_none(self) -> FFMachineInfo | None:
        """Call `get()`, absorbing a response error into a None for the convenience wrappers."""
        try:
            return await self.get()
        except FlashForgeResponseError as error:
            logger.warning("Could not read machine info: %s", error)
            return None

    async def get_detail_raw(self) -> dict[str, Any] | None:
        """
        Retrieves the /detail response as the plain decoded JSON dict, with no
        model validation applied.

        This exists so callers can inspect identity fields - above all `pid` -
        without first having to successfully validate the ~50 unrelated fields
        in the payload. A supported printer must never be rejected because of a
        field that has nothing to do with whether it is supported (issue #18).

        Returns:
            The decoded response body, or None if the printer could not be
            reached or answered with a non-200 status.

        Raises:
            FlashForgeResponseError: The printer answered with a body that is
                not decodable JSON.
        """
        payload = {"serialNumber": self.client.serial_number, "checkCode": self.client.check_code}

        try:
            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.DETAIL),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    logger.warning("Non-200 status from the /detail endpoint: %s", response.status)
                    return None
                data = await json_from_response(response)
        except Exception as error:
            logger.warning(
                "Could not reach the printer's /detail endpoint. This is a transport "
                "failure (unreachable printer, timeout, or refused connection), not a "
                "payload the library failed to read. %s",
                error,
            )
            return None

        if not isinstance(data, dict):
            raise FlashForgeResponseError(
                f"The /detail endpoint returned {type(data).__name__}, expected a JSON object",
                endpoint=Endpoints.DETAIL,
            )
        return data

    async def get_detail_response(self) -> DetailResponse | None:
        """
        Retrieves the validated detailed response from the printer's detail endpoint.
        This contains a wealth of information about the printer's current state.

        Returns:
            A DetailResponse object containing the raw printer details, or None
            if the printer could not be reached.

        Raises:
            FlashForgeResponseError: The printer answered, but the body did not
                validate. Callers should surface this differently from a None
                return: None means "we never got an answer", this means "the
                answer was not one we could read", and only the second is
                actionable as a bug report.
        """
        data = await self.get_detail_raw()
        if data is None:
            return None

        try:
            return DetailResponse(**data)
        except Exception as error:
            logger.warning(
                "The printer answered /detail with a payload that failed validation. This "
                "is NOT a connectivity problem - please report it with the debug dump "
                "below. %s",
                error,
            )
            # Redacted: this dump carries the MAC, IP and cloud registration
            # codes, and it exists to be pasted into a bug report.
            logger.debug("Payload that failed validation: %s", redact_model(data))
            raise FlashForgeResponseError(
                "The printer's /detail response could not be validated",
                endpoint=Endpoints.DETAIL,
                cause=error,
            ) from error
