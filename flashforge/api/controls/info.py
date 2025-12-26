"""
FlashForge Python API - Info Module
"""
from typing import TYPE_CHECKING, Optional

import aiohttp

from ...models.machine_info import FFMachineInfo, MachineState
from ...models.responses import DetailResponse
from ..constants.endpoints import Endpoints

if TYPE_CHECKING:
    from ...client import FlashForgeClient


class MachineInfoParser:
    """
    Transforms printer detail data from the API response format into a structured FFMachineInfo object.
    This class centralizes the logic for mapping and calculating various properties of the printer's state
    and capabilities based on the raw data received from the printer.
    """

    @staticmethod
    def from_detail(detail) -> Optional[FFMachineInfo]:
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
            # Helper function to format time from seconds
            def format_time_from_seconds(seconds: float) -> str:
                try:
                    valid_seconds = int(seconds) if isinstance(seconds, (int, float)) else 0
                    hours = valid_seconds // 3600
                    minutes = (valid_seconds % 3600) // 60
                    return f"{hours:02d}:{minutes:02d}"
                except Exception:
                    return "00:00"

            # Helper function to get machine state
            def get_machine_state(status: str) -> MachineState:
                valid_status = status.lower() if isinstance(status, str) else ""
                state_mapping = {
                    "ready": MachineState.READY,
                    "busy": MachineState.BUSY,
                    "calibrate_doing": MachineState.CALIBRATING,
                    "error": MachineState.ERROR,
                    "heating": MachineState.HEATING,
                    "printing": MachineState.PRINTING,
                    "pausing": MachineState.PAUSING,
                    "paused": MachineState.PAUSED,
                    "cancel": MachineState.CANCELLED,
                    "completed": MachineState.COMPLETED,
                }

                if valid_status in state_mapping:
                    return state_mapping[valid_status]

                if valid_status:
                    print(f"Unknown machine status received: '{status}'")
                return MachineState.UNKNOWN

            # Calculate derived values
            print_eta = format_time_from_seconds(getattr(detail, "estimated_time", 0) or 0)
            formatted_run_time = format_time_from_seconds(getattr(detail, "print_duration", 0) or 0)

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
                name=getattr(detail, "name", "") or "",
                is_pro="Pro" in (getattr(detail, "name", "") or ""),
                is_ad5x="AD5X" in (getattr(detail, "name", "") or "").upper(),
                nozzle_size=getattr(detail, "nozzle_model", "") or "",

                # Temperatures
                print_bed={
                    "current": getattr(detail, "plat_temp", 0) or 0,
                    "set": getattr(detail, "plat_target_temp", 0) or 0
                },
                extruder={
                    "current": getattr(detail, "right_temp", 0) or 0,
                    "set": getattr(detail, "right_target_temp", 0) or 0
                },

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
                machine_state=get_machine_state(getattr(detail, "status", "") or ""),
                status=getattr(detail, "status", "") or "",
                total_print_layers=getattr(detail, "target_print_layer", 0) or 0,
                tvoc=getattr(detail, "tvoc", 0) or 0,
                z_axis_compensation=getattr(detail, "z_axis_compensation", 0) or 0,

                # Cloud codes
                flash_cloud_register_code=getattr(detail, "flash_register_code", "") or "",
                polar_cloud_register_code=getattr(detail, "polar_register_code", "") or "",

                # Extras
                print_eta=print_eta,
                formatted_run_time=formatted_run_time,
                formatted_total_run_time=formatted_total_run_time,

                # AD5X Material Station
                has_matl_station=getattr(detail, "has_matl_station", None),
                matl_station_info=getattr(detail, "matl_station_info", None),
                indep_matl_info=getattr(detail, "indep_matl_info", None),
            )

            return machine_info

        except Exception as error:
            print(f"Error in MachineInfoParser.from_detail: {error}")
            print(f"Detail object causing error: {detail}")
            return None


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

    async def get(self) -> Optional[FFMachineInfo]:
        """
        Retrieves comprehensive machine information, processed into the FFMachineInfo model.
        This method fetches detailed data from the printer and transforms it.
        
        Returns:
            An FFMachineInfo object, or None if an error occurs or no data is returned.
        """
        detail_response = await self.get_detail_response()
        if detail_response and detail_response.detail:
            return MachineInfoParser.from_detail(detail_response.detail)
        return None

    async def is_printing(self) -> bool:
        """
        Checks if the printer is currently in the "printing" state.
        
        Returns:
            True if the printer is printing, False otherwise or if status cannot be determined.
        """
        info = await self.get()
        return info.status == "printing" if info else False

    async def get_status(self) -> Optional[str]:
        """
        Retrieves the raw status string of the printer (e.g., "ready", "printing", "error").
        
        Returns:
            The status string, or None if it cannot be determined.
        """
        info = await self.get()
        return info.status if info else None

    async def get_machine_state(self) -> Optional[MachineState]:
        """
        Retrieves the machine state as a MachineState enum value.
        
        Returns:
            A MachineState enum value, or None if it cannot be determined.
        """
        info = await self.get()
        return info.machine_state if info else None

    async def get_detail_response(self) -> Optional[DetailResponse]:
        """
        Retrieves the raw detailed response from the printer's detail endpoint.
        This contains a wealth of information about the printer's current state.
        
        Returns:
            A DetailResponse object containing the raw printer details,
            or None if the request fails or an error occurs.
        """
        payload = {
            "serialNumber": self.client.serial_number,
            "checkCode": self.client.check_code
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.client.get_endpoint(Endpoints.DETAIL),
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        print(f"Non-200 status from detail endpoint: {response.status}")
                        return None

                    # Fix for FlashForge printer's malformed Content-Type header
                    # Some printers return "appliation/json" instead of "application/json"
                    # We'll manually parse the text as JSON to bypass Content-Type validation
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        # Fallback: manually parse as JSON if Content-Type is malformed
                        text = await response.text()
                        import json
                        data = json.loads(text)
                    
                    return DetailResponse(**data)

        except Exception as error:
            print(f"GetDetailResponse Request error: {error}")
            return None
