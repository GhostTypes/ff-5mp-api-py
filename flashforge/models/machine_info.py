"""
FlashForge Python API - Data Models
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Validation policy for inbound firmware payloads
# ---------------------------------------------------------------------------
#
# Models parsed FROM the printer carry types but NOT value ranges, and no
# required fields beyond what we genuinely cannot work without. The reason is
# blast radius: pydantic fails a model as a unit, and `Info.get_detail_response`
# turns any failure into "no data", which Home Assistant shows as an offline
# printer. So a `ge=0` on a field nobody reads could take the whole integration
# down. That is exactly what happened in issue #18, where a Creator 5 reporting
# `chamberTemp: -108` made every entity unavailable and the config flow report
# `cannot_connect`.
#
# Range constraints belong on OUTBOUND command models (see responses.py), where
# the values are ours and a bad one is our bug. Inbound, we take what we need
# and tolerate the rest. This mirrors the TypeScript client (ff-5mp-api-ts),
# which has never hit this class of failure.
#
# Firmware signals "this sensor does not exist" with an out-of-band negative
# sentinel rather than by omitting the field: -108 on a chamber-less Creator 5,
# and -100 is our own "heater off" value (TempControl.TEMP_OFF). Anything at or
# below this floor is a marker, not a reading.
TEMP_SENTINEL_FLOOR = -50.0

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def sanitize_temperature(value: Any) -> Any:
    """
    Map firmware temperature sentinels to None, passing everything else through.

    Non-numeric input is returned untouched so normal type validation still
    reports it. Used as a `mode="before"` validator on every inbound
    temperature field.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    return None if value <= TEMP_SENTINEL_FLOOR else value


def _normalize_hex_color(value: Any) -> Any:
    """
    Coerce a material color into `#RRGGBB`, or an empty string when it is not
    recognizable.

    Never raises. An unparseable color costs a swatch its color; it must not
    cost the caller the entire /detail response.
    """
    if not isinstance(value, str):
        return "" if value is None else value

    candidate = value.strip()
    if candidate == "" or _HEX_COLOR_RE.match(candidate):
        return candidate

    # Accept the shorthand `#RGB` form by expanding it, and a bare `RRGGBB`
    # without the leading hash - both are plausible firmware variations.
    if re.match(r"^#[0-9A-Fa-f]{3}$", candidate):
        return "#" + "".join(char * 2 for char in candidate[1:])
    if re.match(r"^[0-9A-Fa-f]{6}$", candidate):
        return f"#{candidate}"
    return ""


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

    # `extra="forbid"` deliberately: this model is never parsed from a printer
    # payload, only constructed by MachineInfoParser.from_detail. Forbidding
    # extras there catches a typo'd keyword argument in our own parser, which
    # `extra="allow"` would silently absorb.
    model_config = ConfigDict(extra="forbid")

    # No range constraints: MachineInfoParser feeds these straight from firmware
    # values, so a range here fails `from_detail` for the same reason a range on
    # FFPrinterDetail fails the response - one odd reading, no data at all.
    current: float = Field(default=0.0, description="The current temperature in Celsius")
    set: float = Field(default=0.0, description="The target (set) temperature in Celsius")


class SlotInfo(BaseModel):
    """Information about a single slot in the material station."""

    # `extra="allow"`: inbound, nested under FFPrinterDetail.matl_station_info.
    # FFPrinterDetail allowing extras is not enough on its own - a new field on
    # a *child* fails validation for the whole /detail response, and
    # `Info.get_detail_response` swallows that and returns None, which the HA
    # integration reports as "could not retrieve printer information".
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Every field defaulted: a slot missing one attribute must cost that
    # attribute, not the whole /detail response. `slot_id` carries no 1-4 range
    # for the same reason - a station reporting a fifth slot should show up as a
    # slot we ignore, not as an offline printer.
    has_filament: bool = Field(
        default=False,
        alias="hasFilament",
        description="Indicates if filament is present in this slot",
    )
    material_color: str = Field(
        default="",
        alias="materialColor",
        description="Color of the material in this slot (e.g., '#FFFFFF')",
    )
    material_name: str = Field(
        default="",
        alias="materialName",
        description="Name of the material in this slot (e.g., 'PLA')",
    )
    slot_id: int = Field(default=0, alias="slotId", description="Identifier for this slot (1-4)")

    @field_validator("material_color", mode="before")
    @classmethod
    def normalize_material_color(cls, v: Any) -> Any:
        """Normalize the material color, falling back to '' rather than raising."""
        return _normalize_hex_color(v)


class MatlStationInfo(BaseModel):
    """Detailed information about the material station."""

    # `extra="allow"`: inbound, see SlotInfo.
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Defaulted and unconstrained throughout, per the inbound policy at the top
    # of this module. `slot_infos` in particular had `min_length=1`, which made
    # an explicitly empty `slotInfos: []` - a station with nothing loaded - fail
    # the entire /detail response.
    current_load_slot: int = Field(
        default=0, alias="currentLoadSlot", description="Currently loading slot ID (0 if none)"
    )
    current_slot: int = Field(
        default=0, alias="currentSlot", description="Currently active/printing slot ID (0 if none)"
    )
    slot_cnt: int = Field(
        default=0, alias="slotCnt", description="Total number of slots in the station"
    )
    slot_infos: list[SlotInfo] = Field(
        default_factory=list,
        alias="slotInfos",
        description="Array of information for each slot",
    )
    state_action: int = Field(
        default=0, alias="stateAction", description="Current action state of the material station"
    )
    state_step: int = Field(
        default=0, alias="stateStep", description="Current step within the state action"
    )


class IndepMatlInfo(BaseModel):
    """Information related to independent material loading, often used when a single extruder printer has a material station."""

    # `extra="allow"`: inbound, see SlotInfo.
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    material_color: str = Field(
        default="", alias="materialColor", description="Color of the material"
    )
    material_name: str = Field(
        default="",
        alias="materialName",
        description="Name of the material (can be '?' if unknown)",
    )
    state_action: int = Field(default=0, alias="stateAction", description="Current action state")
    state_step: int = Field(
        default=0, alias="stateStep", description="Current step within the state action"
    )

    @field_validator("material_color", mode="before")
    @classmethod
    def normalize_material_color(cls, v: Any) -> Any:
        """Normalize the material color, falling back to '' rather than raising."""
        return _normalize_hex_color(v)


class FFGcodeToolData(BaseModel):
    """Represents data for a single tool/material used in a G-code file, typically part of a multi-material print."""

    # `extra="allow"`: inbound, nested under FFGcodeFileEntry - which already
    # allows extras, but a child that forbids them reintroduces the same
    # names-only fallback it was flipped to avoid.
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    filament_weight: float = Field(
        default=0.0,
        alias="filamentWeight",
        description="Calculated filament weight for this tool/material in the print",
    )
    material_color: str = Field(
        default="", alias="materialColor", description="Material color hex string (e.g., '#FFFF00')"
    )
    material_name: str = Field(
        default="", alias="materialName", description="Name of the material (e.g., 'PLA')"
    )
    slot_id: int = Field(
        default=0,
        alias="slotId",
        description="Slot ID from the material station, if applicable (0 if not or direct)",
    )
    tool_id: int = Field(default=0, alias="toolId", description="Tool ID or extruder number (0-3)")

    @field_validator("material_color", mode="before")
    @classmethod
    def normalize_material_color(cls, v: Any) -> Any:
        """Normalize the material color, falling back to '' rather than raising."""
        return _normalize_hex_color(v)


class FFGcodeFileEntry(BaseModel):
    """Represents a single G-code file entry as returned by the /gcodeList endpoint, especially for printers like AD5X that provide detailed material info."""

    # `extra="allow"`, matching FFPrinterDetail: a firmware update that adds one
    # field must not fail validation, because Files.get_recent_file_list falls
    # back to a names-only list when it does - silently dropping print time,
    # filament weight, and the per-tool material data for EVERY file.
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # `gcode_file_name` stays required - it is the one field without which the
    # entry means nothing, so failing here is honest. Everything else is
    # metadata and gets a default.
    gcode_file_name: str = Field(
        alias="gcodeFileName", description="The name of the G-code file (e.g., 'FISH_PLA.3mf')"
    )
    gcode_tool_cnt: int | None = Field(
        default=None,
        alias="gcodeToolCnt",
        description="Number of tools/materials used in this G-code file",
    )
    gcode_tool_datas: list[FFGcodeToolData] | None = Field(
        default=None,
        alias="gcodeToolDatas",
        description="Array of detailed information for each tool/material",
    )
    printing_time: int = Field(
        default=0, alias="printingTime", description="Estimated printing time in seconds"
    )
    total_filament_weight: float | None = Field(
        default=None,
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

    model_config = ConfigDict(extra="allow")

    auto_shutdown: str | None = Field(default=None, alias="autoShutdown")
    auto_shutdown_time: int | None = Field(default=None, alias="autoShutdownTime")
    camera: int | None = Field(default=None, alias="camera")
    camera_stream_url: str | None = Field(default=None, alias="cameraStreamUrl")
    chamber_fan_speed: int | None = Field(default=None, alias="chamberFanSpeed")
    chamber_target_temp: float | None = Field(default=None, alias="chamberTargetTemp")
    chamber_temp: float | None = Field(default=None, alias="chamberTemp")
    clear_fan_status: str | None = Field(default=None, alias="clearFanStatus")
    cooling_fan_speed: int | None = Field(default=None, alias="coolingFanSpeed")
    cooling_fan_left_speed: int | None = Field(default=None, alias="coolingFanLeftSpeed")
    coordinate: list[float] | None = Field(default=None, alias="coordinate")
    cumulative_filament: float | None = Field(default=None, alias="cumulativeFilament")
    cumulative_print_time: int | None = Field(default=None, alias="cumulativePrintTime")
    current_print_speed: int | None = Field(default=None, alias="currentPrintSpeed")
    door_status: str | None = Field(default=None, alias="doorStatus")
    error_code: str | None = Field(default=None, alias="errorCode")
    estimated_left_len: float | None = Field(default=None, alias="estimatedLeftLen")
    estimated_left_weight: float | None = Field(default=None, alias="estimatedLeftWeight")
    estimated_right_len: float | None = Field(default=None, alias="estimatedRightLen")
    estimated_right_weight: float | None = Field(default=None, alias="estimatedRightWeight")
    estimated_time: float | None = Field(default=None, alias="estimatedTime")
    extrude_ctrl: int | None = Field(default=None, alias="extrudeCtrl")
    external_fan_status: str | None = Field(default=None, alias="externalFanStatus")
    fill_amount: float | None = Field(default=None, alias="fillAmount")
    firmware_version: str | None = Field(default=None, alias="firmwareVersion")
    flash_register_code: str | None = Field(default=None, alias="flashRegisterCode")
    # AD5X-only, and firmware omits what does not apply: the Creator 5 series
    # leaves this out of /detail even with four loaded slots, so None means "not
    # reported", NOT "no station". Never gate a feature on it - read the derived
    # FFMachineInfo.has_matl_station, or check matl_station_info yourself.
    has_matl_station: bool | None = Field(default=None, alias="hasMatlStation")
    matl_station_info: MatlStationInfo | None = Field(default=None, alias="matlStationInfo")
    indep_matl_info: IndepMatlInfo | None = Field(default=None, alias="indepMatlInfo")
    has_left_filament: bool | None = Field(default=None, alias="hasLeftFilament")
    has_right_filament: bool | None = Field(default=None, alias="hasRightFilament")
    internal_fan_status: str | None = Field(default=None, alias="internalFanStatus")
    ip_addr: str | None = Field(default=None, alias="ipAddr")
    left_filament_type: str | None = Field(default=None, alias="leftFilamentType")
    left_target_temp: float | None = Field(default=None, alias="leftTargetTemp")
    left_temp: float | None = Field(default=None, alias="leftTemp")
    light_status: str | None = Field(default=None, alias="lightStatus")
    location: str | None = Field(default=None, alias="location")
    mac_addr: str | None = Field(default=None, alias="macAddr")
    measure: str | None = Field(default=None, alias="measure")
    move_ctrl: int | None = Field(default=None, alias="moveCtrl")
    name: str | None = Field(default=None, alias="name")
    nozzle_cnt: int | None = Field(default=None, alias="nozzleCnt")
    nozzle_model: str | None = Field(default=None, alias="nozzleModel")
    nozzle_style: int | None = Field(default=None, alias="nozzleStyle")
    # --- Creator 5 series raw fields ---
    # Immutable factory model name (e.g. "Creator 5 Pro"); unlike `name` this is
    # not user-editable. May be absent on older firmware.
    model: str | None = Field(default=None, alias="model")
    # Per-tool current nozzle temperatures (one entry per nozzle). Multi-nozzle
    # Creator 5 series report these; single-nozzle models use rightTemp/leftTemp.
    # Entries are nullable because a sentinel reading is normalized to None by
    # `drop_nozzle_temperature_sentinels` below.
    nozzle_temps: list[float | None] | None = Field(default=None, alias="nozzleTemps")
    # Per-tool target nozzle temperatures (one entry per nozzle).
    nozzle_target_temps: list[float | None] | None = Field(
        default=None, alias="nozzleTargetTemps"
    )
    # Lidar / first-layer scanner presence flag (1 = present, 0 = absent).
    lidar: int | None = Field(default=None, alias="lidar")
    pid: int | None = Field(default=None, alias="pid")
    plat_target_temp: float | None = Field(default=None, alias="platTargetTemp")
    plat_temp: float | None = Field(default=None, alias="platTemp")
    polar_register_code: str | None = Field(default=None, alias="polarRegisterCode")
    print_duration: int | None = Field(default=None, alias="printDuration")
    print_file_name: str | None = Field(default=None, alias="printFileName")
    print_file_thumb_url: str | None = Field(default=None, alias="printFileThumbUrl")
    print_layer: int | None = Field(default=None, alias="printLayer")
    print_progress: float | None = Field(default=None, alias="printProgress")
    print_speed_adjust: int | None = Field(default=None, alias="printSpeedAdjust")
    remaining_disk_space: float | None = Field(default=None, alias="remainingDiskSpace")
    right_filament_type: str | None = Field(default=None, alias="rightFilamentType")
    right_target_temp: float | None = Field(default=None, alias="rightTargetTemp")
    right_temp: float | None = Field(default=None, alias="rightTemp")
    status: str | None = Field(default=None, alias="status")
    target_print_layer: int | None = Field(default=None, alias="targetPrintLayer")
    tvoc: float | None = Field(default=None, alias="tvoc")
    z_axis_compensation: float | None = Field(default=None, alias="zAxisCompensation")

    # Firmware reports absent temperature hardware with a negative sentinel
    # (-108 on a chamber-less Creator 5, issue #18) rather than by omitting the
    # field. Map those to None here so "no sensor" reads as "not reported"
    # everywhere downstream, instead of as a -108 C reading or a hard failure.
    @field_validator(
        "chamber_temp",
        "chamber_target_temp",
        "left_temp",
        "left_target_temp",
        "plat_temp",
        "plat_target_temp",
        "right_temp",
        "right_target_temp",
        mode="before",
    )
    @classmethod
    def drop_temperature_sentinels(cls, v: Any) -> Any:
        """Replace out-of-band 'no sensor' temperature markers with None."""
        return sanitize_temperature(v)

    @field_validator("nozzle_temps", "nozzle_target_temps", mode="before")
    @classmethod
    def drop_nozzle_temperature_sentinels(cls, v: Any) -> Any:
        """Apply the same sentinel handling to the per-tool temperature arrays."""
        if not isinstance(v, list):
            return v
        return [sanitize_temperature(entry) for entry in v]


class FFMachineInfo(BaseModel):
    """
    Represents a structured and user-friendly model of the printer's information and state.
    This interface is populated by transforming data from FFPrinterDetail.
    """

    # `extra="forbid"` deliberately: see Temperature. Built only at
    # `MachineInfoParser.from_detail`, from ~50 keyword arguments, never from
    # raw printer JSON - so forbidding extras is a typo check on our own code,
    # not a firmware-compatibility risk.
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
    pid: int | None = None
    is_pro: bool = False
    is_ad5x: bool = False
    # Creator 5 / Creator 5 Pro (4-head tool-changer) detection. Drives the
    # http_only transport decision and Pro-only capabilities (door sensor).
    is_creator5: bool = False
    is_creator5_pro: bool = False
    # Immutable factory model name (e.g. "Creator 5 Pro"). Falls back to a
    # PID-derived name, then the user-set `name`, when the printer doesn't
    # report the `model` field.
    model: str | None = None
    nozzle_size: str = ""
    # Number of tools/nozzles the printer reports. Creator 5 series = 4
    # (tool-changer); single-nozzle models = 1. Mirrors len(tool_temps).
    nozzle_count: int | None = None

    # Temperatures
    print_bed: Temperature = Field(default_factory=Temperature)
    extruder: Temperature = Field(default_factory=Temperature)
    # Heated chamber. Only the Creator 5 series has one; other models report 0/0.
    chamber: Temperature | None = None
    # Current/target temperatures for every tool/nozzle. Single-nozzle models
    # report a 1-element array mirroring `extruder`; Creator 5 series report
    # one entry per nozzle.
    tool_temps: list[Temperature] = Field(default_factory=list)

    # Capability flags (presence-derived, never assumed from model family)
    has_camera: bool = False
    has_lidar: bool = False
    # Only true on models with confirmed hardware (Creator 5 Pro). When false,
    # `door_open` is cosmetic and should not be surfaced.
    has_door_sensor: bool = False
    # True only when the printer actually reported a chamber temperature. The
    # heated chamber is a Creator 5 series *option*, not a family trait: units
    # without it report the -108 sentinel, which FFPrinterDetail normalizes to
    # None. Gate chamber entities on this, never on `is_creator5`.
    has_chamber_sensor: bool = False

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

    # Material Station (AD5X / Creator 5 series)
    #
    # A capability, not a passthrough: MachineInfoParser DERIVES this from the
    # station data rather than copying the raw `hasMatlStation` field, which the
    # Creator 5 series never reports even with a station attached. It is a plain
    # bool on purpose - there is no "unknown" state to represent, and offering
    # one is what let an unreported flag read as absent hardware. For the
    # untouched firmware value, read FFPrinterDetail.has_matl_station.
    has_matl_station: bool = False
    matl_station_info: MatlStationInfo | None = None
    indep_matl_info: IndepMatlInfo | None = None

    @model_validator(mode="after")
    def validate_print_progress(self) -> FFMachineInfo:
        """Ensure print progress integer matches float value."""
        if self.print_progress is not None:
            self.print_progress_int = max(0, min(100, int(self.print_progress * 100)))
        return self
