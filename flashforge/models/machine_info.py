"""
FlashForge Python API - Data Models
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MachineState(Enum):
    """Enumerates the possible operational states of the FlashForge 3D printer."""
    READY = "ready"
    BUSY = "busy"
    CALIBRATING = "calibrating"
    ERROR = "error"
    HEATING = "heating"
    PRINTING = "printing"
    PAUSING = "pausing"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


class Temperature(BaseModel):
    """Represents a pair of current and target temperatures for a component like an extruder or print bed."""
    current: float = Field(default=0.0, description="The current temperature in Celsius")
    set: float = Field(default=0.0, description="The target (set) temperature in Celsius")


class FFPrinterDetail(BaseModel):
    """
    Represents the raw detailed information about a FlashForge 3D printer as obtained from its API.
    Properties are often in the printer's native naming format and may include string representations
    of boolean states (e.g., "open", "close").
    """
    auto_shutdown: Optional[str] = Field(default=None, alias="autoShutdown")
    auto_shutdown_time: Optional[int] = Field(default=None, alias="autoShutdownTime")
    camera_stream_url: Optional[str] = Field(default=None, alias="cameraStreamUrl")
    chamber_fan_speed: Optional[int] = Field(default=None, alias="chamberFanSpeed")
    chamber_target_temp: Optional[float] = Field(default=None, alias="chamberTargetTemp")
    chamber_temp: Optional[float] = Field(default=None, alias="chamberTemp")
    cooling_fan_speed: Optional[int] = Field(default=None, alias="coolingFanSpeed")
    cumulative_filament: Optional[float] = Field(default=None, alias="cumulativeFilament")
    cumulative_print_time: Optional[int] = Field(default=None, alias="cumulativePrintTime")
    current_print_speed: Optional[int] = Field(default=None, alias="currentPrintSpeed")
    door_status: Optional[str] = Field(default=None, alias="doorStatus")
    error_code: Optional[str] = Field(default=None, alias="errorCode")
    estimated_left_len: Optional[float] = Field(default=None, alias="estimatedLeftLen")
    estimated_left_weight: Optional[float] = Field(default=None, alias="estimatedLeftWeight")
    estimated_right_len: Optional[float] = Field(default=None, alias="estimatedRightLen")
    estimated_right_weight: Optional[float] = Field(default=None, alias="estimatedRightWeight")
    estimated_time: Optional[int] = Field(default=None, alias="estimatedTime")
    external_fan_status: Optional[str] = Field(default=None, alias="externalFanStatus")
    fill_amount: Optional[float] = Field(default=None, alias="fillAmount")
    firmware_version: Optional[str] = Field(default=None, alias="firmwareVersion")
    flash_register_code: Optional[str] = Field(default=None, alias="flashRegisterCode")
    internal_fan_status: Optional[str] = Field(default=None, alias="internalFanStatus")
    ip_addr: Optional[str] = Field(default=None, alias="ipAddr")
    left_filament_type: Optional[str] = Field(default=None, alias="leftFilamentType")
    left_target_temp: Optional[float] = Field(default=None, alias="leftTargetTemp")
    left_temp: Optional[float] = Field(default=None, alias="leftTemp")
    light_status: Optional[str] = Field(default=None, alias="lightStatus")
    location: Optional[str] = Field(default=None, alias="location")
    mac_addr: Optional[str] = Field(default=None, alias="macAddr")
    measure: Optional[str] = Field(default=None, alias="measure")
    name: Optional[str] = Field(default=None, alias="name")
    nozzle_cnt: Optional[int] = Field(default=None, alias="nozzleCnt")
    nozzle_model: Optional[str] = Field(default=None, alias="nozzleModel")
    nozzle_style: Optional[int] = Field(default=None, alias="nozzleStyle")
    pid: Optional[int] = Field(default=None, alias="pid")
    plat_target_temp: Optional[float] = Field(default=None, alias="platTargetTemp")
    plat_temp: Optional[float] = Field(default=None, alias="platTemp")
    polar_register_code: Optional[str] = Field(default=None, alias="polarRegisterCode")
    print_duration: Optional[int] = Field(default=None, alias="printDuration")
    print_file_name: Optional[str] = Field(default=None, alias="printFileName")
    print_file_thumb_url: Optional[str] = Field(default=None, alias="printFileThumbUrl")
    print_layer: Optional[int] = Field(default=None, alias="printLayer")
    print_progress: Optional[float] = Field(default=None, alias="printProgress")
    print_speed_adjust: Optional[int] = Field(default=None, alias="printSpeedAdjust")
    remaining_disk_space: Optional[float] = Field(default=None, alias="remainingDiskSpace")
    right_filament_type: Optional[str] = Field(default=None, alias="rightFilamentType")
    right_target_temp: Optional[float] = Field(default=None, alias="rightTargetTemp")
    right_temp: Optional[float] = Field(default=None, alias="rightTemp")
    status: Optional[str] = Field(default=None, alias="status")
    target_print_layer: Optional[int] = Field(default=None, alias="targetPrintLayer")
    tvoc: Optional[float] = Field(default=None, alias="tvoc")
    z_axis_compensation: Optional[float] = Field(default=None, alias="zAxisCompensation")


class FFMachineInfo(BaseModel):
    """
    Represents a structured and user-friendly model of the printer's information and state.
    This interface is populated by transforming data from FFPrinterDetail.
    """
    # Auto-shutdown settings
    auto_shutdown: bool = False
    auto_shutdown_time: int = 0

    # Camera
    camera_stream_url: str = ""

    # Fan speeds
    chamber_fan_speed: int = 0
    cooling_fan_speed: int = 0

    # Cumulative stats
    cumulative_filament: float = 0.0
    cumulative_print_time: int = 0

    # Current print speed
    current_print_speed: int = 0

    # Disk space
    free_disk_space: str = "0.00"

    # Door and error status
    door_open: bool = False
    error_code: str = ""

    # Current print estimates
    est_length: float = 0.0
    est_weight: float = 0.0
    estimated_time: int = 0

    # Fans & LED status
    external_fan_on: bool = False
    internal_fan_on: bool = False
    lights_on: bool = False

    # Network
    ip_address: str = ""
    mac_address: str = ""

    # Print settings
    fill_amount: float = 0.0
    firmware_version: str = ""
    name: str = ""
    is_pro: bool = False
    nozzle_size: str = ""

    # Temperatures
    print_bed: Temperature = Field(default_factory=Temperature)
    extruder: Temperature = Field(default_factory=Temperature)

    # Current print stats
    print_duration: int = 0
    print_file_name: str = ""
    print_file_thumb_url: str = ""
    current_print_layer: int = 0
    print_progress: float = 0.0
    print_progress_int: int = 0
    print_speed_adjust: int = 0
    filament_type: str = ""

    # Machine state
    machine_state: MachineState = MachineState.UNKNOWN
    status: str = ""
    total_print_layers: int = 0
    tvoc: float = 0.0
    z_axis_compensation: float = 0.0

    # Cloud codes
    flash_cloud_register_code: str = ""
    polar_cloud_register_code: str = ""

    # Extras
    print_eta: str = "00:00"
    completion_time: datetime = Field(default_factory=datetime.now)
    formatted_run_time: str = "00:00"
    formatted_total_run_time: str = "0h:0m"
