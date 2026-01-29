"""
FlashForge Python API - Data Models
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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

    model_config = ConfigDict(extra="forbid")

    current: float = Field(
        default=0.0, ge=-50, le=500, description="The current temperature in Celsius"
    )
    set: float = Field(
        default=0.0, ge=-50, le=500, description="The target (set) temperature in Celsius"
    )


class SlotInfo(BaseModel):
    """Information about a single slot in the material station."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    has_filament: bool = Field(
        alias="hasFilament", description="Indicates if filament is present in this slot"
    )
    material_color: str = Field(
        alias="materialColor", description="Color of the material in this slot (e.g., '#FFFFFF')"
    )
    material_name: str = Field(
        alias="materialName", description="Name of the material in this slot (e.g., 'PLA')"
    )
    slot_id: int = Field(alias="slotId", ge=1, le=4, description="Identifier for this slot (1-4)")

    @field_validator("material_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate that the color is a valid hex color code or empty string."""
        import re

        if v == "" or re.match(r"^#[0-9A-Fa-f]{6}$", v):
            return v
        raise ValueError(f"Invalid hex color format: {v}")


class MatlStationInfo(BaseModel):
    """Detailed information about the material station."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    current_load_slot: int = Field(
        alias="currentLoadSlot", ge=0, le=4, description="Currently loading slot ID (0 if none)"
    )
    current_slot: int = Field(
        alias="currentSlot", ge=0, le=4, description="Currently active/printing slot ID (0 if none)"
    )
    slot_cnt: int = Field(
        alias="slotCnt", ge=1, le=4, description="Total number of slots in the station"
    )
    slot_infos: list[SlotInfo] = Field(
        min_length=1,
        max_length=4,
        default_factory=list,
        alias="slotInfos",
        description="Array of information for each slot",
    )
    state_action: int = Field(
        alias="stateAction", ge=0, description="Current action state of the material station"
    )
    state_step: int = Field(
        alias="stateStep", ge=0, description="Current step within the state action"
    )


class IndepMatlInfo(BaseModel):
    """Information related to independent material loading, often used when a single extruder printer has a material station."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    material_color: str = Field(alias="materialColor", description="Color of the material")
    material_name: str = Field(
        alias="materialName", description="Name of the material (can be '?' if unknown)"
    )
    state_action: int = Field(alias="stateAction", ge=0, description="Current action state")
    state_step: int = Field(
        alias="stateStep", ge=0, description="Current step within the state action"
    )

    @field_validator("material_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate that the color is a valid hex color code or empty string."""
        import re

        if v == "" or re.match(r"^#[0-9A-Fa-f]{6}$", v):
            return v
        raise ValueError(f"Invalid hex color format: {v}")


class FFGcodeToolData(BaseModel):
    """Represents data for a single tool/material used in a G-code file, typically part of a multi-material print."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    filament_weight: float = Field(
        alias="filamentWeight",
        ge=0,
        description="Calculated filament weight for this tool/material in the print",
    )
    material_color: str = Field(
        alias="materialColor", description="Material color hex string (e.g., '#FFFF00')"
    )
    material_name: str = Field(
        alias="materialName", description="Name of the material (e.g., 'PLA')"
    )
    slot_id: int = Field(
        alias="slotId",
        ge=0,
        le=4,
        description="Slot ID from the material station, if applicable (0 if not or direct)",
    )
    tool_id: int = Field(alias="toolId", ge=0, le=3, description="Tool ID or extruder number (0-3)")

    @field_validator("material_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate that the color is a valid hex color code or empty string."""
        import re

        if v == "" or re.match(r"^#[0-9A-Fa-f]{6}$", v):
            return v
        raise ValueError(f"Invalid hex color format: {v}")


class FFGcodeFileEntry(BaseModel):
    """Represents a single G-code file entry as returned by the /gcodeList endpoint, especially for printers like AD5X that provide detailed material info."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    gcode_file_name: str = Field(
        alias="gcodeFileName", description="The name of the G-code file (e.g., 'FISH_PLA.3mf')"
    )
    gcode_tool_cnt: int | None = Field(
        default=None,
        ge=0,
        le=4,
        alias="gcodeToolCnt",
        description="Number of tools/materials used in this G-code file",
    )
    gcode_tool_datas: list[FFGcodeToolData] | None = Field(
        default=None,
        max_length=4,
        alias="gcodeToolDatas",
        description="Array of detailed information for each tool/material",
    )
    printing_time: int = Field(
        alias="printingTime", ge=0, description="Estimated printing time in seconds"
    )
    total_filament_weight: float | None = Field(
        default=None,
        ge=0,
        alias="totalFilamentWeight",
        description="Total estimated filament weight for the print",
    )
    use_matl_station: bool | None = Field(
        default=None,
        alias="useMatlStation",
        description="Indicates if the G-code file is intended for use with a material station",
    )


class FFPrinterDetail(BaseModel):
    """
    Represents the raw detailed information about a FlashForge 3D printer as obtained from its API.
    Properties are often in the printer's native naming format and may include string representations
    of boolean states (e.g., "open", "close").
    """

    model_config = ConfigDict(extra="forbid")

    auto_shutdown: str | None = Field(default=None, alias="autoShutdown")
    auto_shutdown_time: int | None = Field(default=None, ge=0, alias="autoShutdownTime")
    camera_stream_url: str | None = Field(default=None, alias="cameraStreamUrl")
    chamber_fan_speed: int | None = Field(default=None, ge=0, le=100, alias="chamberFanSpeed")
    chamber_target_temp: float | None = Field(
        default=None, ge=-50, le=500, alias="chamberTargetTemp"
    )
    chamber_temp: float | None = Field(default=None, ge=-50, le=500, alias="chamberTemp")
    cooling_fan_speed: int | None = Field(default=None, ge=0, le=100, alias="coolingFanSpeed")
    cooling_fan_left_speed: int | None = Field(
        default=None, ge=0, le=100, alias="coolingFanLeftSpeed"
    )
    cumulative_filament: float | None = Field(default=None, ge=0, alias="cumulativeFilament")
    cumulative_print_time: int | None = Field(default=None, ge=0, alias="cumulativePrintTime")
    current_print_speed: int | None = Field(default=None, ge=0, le=200, alias="currentPrintSpeed")
    door_status: str | None = Field(default=None, alias="doorStatus")
    error_code: str | None = Field(default=None, alias="errorCode")
    estimated_left_len: float | None = Field(default=None, ge=0, alias="estimatedLeftLen")
    estimated_left_weight: float | None = Field(default=None, ge=0, alias="estimatedLeftWeight")
    estimated_right_len: float | None = Field(default=None, ge=0, alias="estimatedRightLen")
    estimated_right_weight: float | None = Field(default=None, ge=0, alias="estimatedRightWeight")
    estimated_time: float | None = Field(default=None, ge=0, alias="estimatedTime")
    external_fan_status: str | None = Field(default=None, alias="externalFanStatus")
    fill_amount: float | None = Field(default=None, ge=0, le=100, alias="fillAmount")
    firmware_version: str | None = Field(default=None, alias="firmwareVersion")
    flash_register_code: str | None = Field(default=None, alias="flashRegisterCode")
    has_matl_station: bool | None = Field(default=None, alias="hasMatlStation")
    matl_station_info: MatlStationInfo | None = Field(default=None, alias="matlStationInfo")
    indep_matl_info: IndepMatlInfo | None = Field(default=None, alias="indepMatlInfo")
    has_left_filament: bool | None = Field(default=None, alias="hasLeftFilament")
    has_right_filament: bool | None = Field(default=None, alias="hasRightFilament")
    internal_fan_status: str | None = Field(default=None, alias="internalFanStatus")
    ip_addr: str | None = Field(default=None, alias="ipAddr")
    left_filament_type: str | None = Field(default=None, alias="leftFilamentType")
    left_target_temp: float | None = Field(default=None, ge=-50, le=500, alias="leftTargetTemp")
    left_temp: float | None = Field(default=None, ge=-50, le=500, alias="leftTemp")
    light_status: str | None = Field(default=None, alias="lightStatus")
    location: str | None = Field(default=None, alias="location")
    mac_addr: str | None = Field(default=None, alias="macAddr")
    measure: str | None = Field(default=None, alias="measure")
    name: str | None = Field(default=None, alias="name")
    nozzle_cnt: int | None = Field(default=None, ge=1, le=4, alias="nozzleCnt")
    nozzle_model: str | None = Field(default=None, alias="nozzleModel")
    nozzle_style: int | None = Field(default=None, ge=0, alias="nozzleStyle")
    pid: int | None = Field(default=None, ge=0, alias="pid")
    plat_target_temp: float | None = Field(default=None, ge=-50, le=500, alias="platTargetTemp")
    plat_temp: float | None = Field(default=None, ge=-50, le=500, alias="platTemp")
    polar_register_code: str | None = Field(default=None, alias="polarRegisterCode")
    print_duration: int | None = Field(default=None, ge=0, alias="printDuration")
    print_file_name: str | None = Field(default=None, alias="printFileName")
    print_file_thumb_url: str | None = Field(default=None, alias="printFileThumbUrl")
    print_layer: int | None = Field(default=None, ge=0, alias="printLayer")
    print_progress: float | None = Field(default=None, ge=0, le=100, alias="printProgress")
    print_speed_adjust: int | None = Field(default=None, ge=0, le=200, alias="printSpeedAdjust")
    remaining_disk_space: float | None = Field(default=None, ge=0, alias="remainingDiskSpace")
    right_filament_type: str | None = Field(default=None, alias="rightFilamentType")
    right_target_temp: float | None = Field(default=None, ge=-50, le=500, alias="rightTargetTemp")
    right_temp: float | None = Field(default=None, ge=-50, le=500, alias="rightTemp")
    status: str | None = Field(default=None, alias="status")
    target_print_layer: int | None = Field(default=None, ge=0, alias="targetPrintLayer")
    tvoc: float | None = Field(default=None, ge=0, alias="tvoc")
    z_axis_compensation: float | None = Field(
        default=None, ge=-10, le=10, alias="zAxisCompensation"
    )


class FFMachineInfo(BaseModel):
    """
    Represents a structured and user-friendly model of the printer's information and state.
    This interface is populated by transforming data from FFPrinterDetail.
    """

    model_config = ConfigDict(extra="forbid")

    # Auto-shutdown settings
    auto_shutdown: bool = False
    auto_shutdown_time: int = 0

    # Camera
    camera_stream_url: str = ""

    # Fan speeds
    chamber_fan_speed: int = 0
    cooling_fan_speed: int = 0
    cooling_fan_left_speed: int | None = None

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
    estimated_time: float = 0.0

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
    is_ad5x: bool = False
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

    # AD5X Material Station
    has_matl_station: bool | None = None
    matl_station_info: MatlStationInfo | None = None
    indep_matl_info: IndepMatlInfo | None = None

    @model_validator(mode="after")
    def validate_print_progress(self) -> FFMachineInfo:
        """Ensure print progress integer matches float value."""
        if self.print_progress is not None:
            self.print_progress_int = int(self.print_progress)
        return self
