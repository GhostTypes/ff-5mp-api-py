"""
Inbound payload leniency.

The rule these tests enforce: a model parsed FROM the printer must never fail
as a unit because of one field. Pydantic validates a model all-or-nothing, and
`Info.get_detail_response` turns a failure into "no data", which Home Assistant
shows as an offline printer - so a range constraint on a field nobody reads can
take the whole integration down.

That is not hypothetical. Issue #18: a Creator 5 with no heated chamber reports
`chamberTemp: -108` (the firmware's "no sensor" sentinel, a sibling of our own
TEMP_OFF = -100). A `ge=-50` on that field made every entity unavailable and
made the config flow report `cannot_connect`, pointing the user at their network
for three releases.
"""

import math

import pytest
from pydantic import ValidationError

from flashforge.api.controls.info import MachineInfoParser
from flashforge.models.machine_info import (
    TEMP_SENTINEL_FLOOR,
    FFGcodeFileEntry,
    FFPrinterDetail,
    MatlStationInfo,
    SlotInfo,
    Temperature,
)
from flashforge.models.responses import DetailResponse

from .fixtures.printer_responses import (
    CREATOR_5_INFO_RESPONSE,
    CREATOR_5_NO_CHAMBER_INFO_RESPONSE,
    CREATOR_5_PRO_MATL_STATION_INFO,
)


# ---------------------------------------------------------------------------
# The reported failure
# ---------------------------------------------------------------------------


def test_chamberless_creator5_detail_parses():
    """The exact issue #18 payload: chamberTemp -108 must not fail /detail."""
    response = DetailResponse(**CREATOR_5_NO_CHAMBER_INFO_RESPONSE)

    assert response.detail is not None
    assert response.detail.pid == 40
    # The sentinel is normalized away rather than surfaced as a -108 C reading.
    assert response.detail.chamber_temp is None


def test_chamberless_creator5_builds_machine_info():
    """The second layer: Temperature must not reject the sentinel either."""
    detail = DetailResponse(**CREATOR_5_NO_CHAMBER_INFO_RESPONSE).detail
    info = MachineInfoParser.from_detail(detail)

    assert info is not None
    assert info.is_creator5 is True
    assert info.has_chamber_sensor is False


def test_creator5_with_chamber_still_reports_the_sensor():
    """A real chamber reading is untouched, and the capability flag follows it."""
    detail = DetailResponse(**CREATOR_5_INFO_RESPONSE).detail
    info = MachineInfoParser.from_detail(detail)

    assert detail.chamber_temp == 45
    assert info.has_chamber_sensor is True
    assert info.chamber.current == 45


@pytest.mark.parametrize("sentinel", [-100, -108, -273, TEMP_SENTINEL_FLOOR - 1])
@pytest.mark.parametrize(
    "field",
    [
        "chamberTemp",
        "chamberTargetTemp",
        "leftTemp",
        "leftTargetTemp",
        "platTemp",
        "platTargetTemp",
        "rightTemp",
        "rightTargetTemp",
    ],
)
def test_every_temperature_field_tolerates_sentinels(field, sentinel):
    """No temperature field may be the one that takes down the response."""
    detail = FFPrinterDetail(**{field: sentinel})
    assert getattr(detail, _snake(field)) is None


def test_nozzle_temp_arrays_tolerate_sentinels():
    """Per-tool arrays carry the sentinel too; entries normalize individually."""
    detail = FFPrinterDetail(
        nozzleTemps=[200.0, -108, 205.0, -100],
        nozzleTargetTemps=[210.0, -108, 210.0, -100],
    )

    assert detail.nozzle_temps == [200.0, None, 205.0, None]

    info = MachineInfoParser.from_detail(detail)
    # A tool with no reading reads as 0, not as -108.
    assert [t.current for t in info.tool_temps] == [200.0, 0.0, 205.0, 0.0]


def _snake(camel: str) -> str:
    """Convert a firmware camelCase alias to our snake_case field name."""
    out = []
    for char in camel:
        if char.isupper():
            out.append("_")
            out.append(char.lower())
        else:
            out.append(char)
    return "".join(out)


# ---------------------------------------------------------------------------
# The general rule, not just the reported field
# ---------------------------------------------------------------------------

# Every numeric field on FFPrinterDetail, with a value far outside anything the
# old constraints allowed. Fixing chamberTemp alone would only have relocated
# the next outage to one of these.
HOSTILE_NUMERIC_VALUES = {
    "autoShutdownTime": -1,
    "camera": -5,
    "chamberFanSpeed": 255,
    "coolingFanSpeed": 255,
    "coolingFanLeftSpeed": -3,
    "cumulativeFilament": -1.0,
    "cumulativePrintTime": -60,
    "currentPrintSpeed": 99999,
    "estimatedLeftLen": -1.0,
    "estimatedLeftWeight": -1.0,
    "estimatedRightLen": -1.0,
    "estimatedRightWeight": -1.0,
    "estimatedTime": -1.0,
    "extrudeCtrl": -1,
    "fillAmount": 200.0,
    "lidar": -1,
    "moveCtrl": -1,
    "nozzleCnt": 9,
    "nozzleStyle": -1,
    "pid": -1,
    "printDuration": -1,
    "printLayer": -1,
    "printProgress": 150.0,
    "printSpeedAdjust": 99999,
    "remainingDiskSpace": -1.0,
    "targetPrintLayer": -1,
    "tvoc": -1.0,
    "zAxisCompensation": -999.0,
}


@pytest.mark.parametrize("field,value", sorted(HOSTILE_NUMERIC_VALUES.items()))
def test_no_single_numeric_field_can_fail_the_response(field, value):
    """One out-of-range field costs that field's accuracy, never the response."""
    payload = {
        **CREATOR_5_INFO_RESPONSE,
        "detail": {**CREATOR_5_INFO_RESPONSE["detail"], field: value},
    }

    response = DetailResponse(**payload)
    assert response.detail is not None
    # And it still converts - a lenient model that then fails downstream would
    # be no improvement.
    assert MachineInfoParser.from_detail(response.detail) is not None


def test_all_hostile_fields_at_once():
    """The whole payload can be wrong at the same time and still yield data."""
    payload = {
        **CREATOR_5_INFO_RESPONSE,
        "detail": {
            **CREATOR_5_INFO_RESPONSE["detail"],
            **HOSTILE_NUMERIC_VALUES,
            "chamberTemp": -108,
        },
    }

    info = MachineInfoParser.from_detail(DetailResponse(**payload).detail)
    assert info is not None
    # pid was clobbered to -1, so the name heuristic has to carry model identity.
    assert info.is_creator5 is True


# ---------------------------------------------------------------------------
# Nested models: a child failure fails the whole /detail response
# ---------------------------------------------------------------------------


def test_slot_info_tolerates_missing_fields():
    """A slot missing every attribute costs the attributes, not the response."""
    slot = SlotInfo()

    assert slot.slot_id == 0
    assert slot.material_name == ""
    assert slot.material_color == ""
    assert slot.has_filament is False


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("#FF0000", "#FF0000"),
        ("", ""),
        ("#f00", "#ff0000"),  # shorthand expanded
        ("FF0000", "#FF0000"),  # missing hash added
        ("transparent", ""),  # unrecognized degrades to no color
        ("not a color", ""),
        (None, ""),
    ],
)
def test_material_color_never_raises(raw, expected):
    """An odd color loses the swatch its color; it must not lose the response."""
    assert SlotInfo(materialColor=raw).material_color == expected


def test_material_station_accepts_empty_slot_list():
    """`slotInfos: []` is a station with nothing loaded, not a broken payload."""
    station = MatlStationInfo(**{**CREATOR_5_PRO_MATL_STATION_INFO, "slotInfos": []})
    assert station.slot_infos == []


def test_material_station_accepts_more_slots_than_we_know_about():
    """A future 5-slot station degrades to slots we ignore, not to no data."""
    slots = CREATOR_5_PRO_MATL_STATION_INFO["slotInfos"]
    station = MatlStationInfo(
        **{
            **CREATOR_5_PRO_MATL_STATION_INFO,
            "slotCnt": 5,
            "slotInfos": [*slots, {"slotId": 5, "hasFilament": True, "materialName": "ABS"}],
        }
    )
    assert len(station.slot_infos) == 5


def test_broken_slot_does_not_fail_the_whole_detail():
    """The end-to-end version: a bad slot must still leave a usable /detail."""
    payload = {
        **CREATOR_5_INFO_RESPONSE,
        "detail": {
            **CREATOR_5_INFO_RESPONSE["detail"],
            "matlStationInfo": {
                **CREATOR_5_PRO_MATL_STATION_INFO,
                "slotInfos": [{"slotId": 1, "materialColor": "rgb(1,2,3)"}],
            },
        },
    }

    info = MachineInfoParser.from_detail(DetailResponse(**payload).detail)
    assert info is not None
    assert info.has_matl_station is True


def test_gcode_entry_keeps_only_filename_required():
    """File metadata is optional; the name is the one thing an entry needs."""
    entry = FFGcodeFileEntry(gcodeFileName="benchy.3mf")
    assert entry.printing_time == 0

    with pytest.raises(ValidationError):
        FFGcodeFileEntry(printingTime=60)


# ---------------------------------------------------------------------------
# What stays strict
# ---------------------------------------------------------------------------


def test_temperature_accepts_any_reading():
    """Temperature is fed from firmware values, so it carries no range either."""
    assert Temperature(current=-108.0, set=9999.0).current == -108.0


def test_type_errors_are_still_errors():
    """Leniency is about ranges and absence, not about accepting nonsense."""
    with pytest.raises(ValidationError):
        FFPrinterDetail(printProgress="not a number")


def test_nan_temperature_is_not_treated_as_a_sentinel():
    """NaN compares false against the floor; it must pass through, not vanish."""
    detail = FFPrinterDetail(chamberTemp=float("nan"))
    assert detail.chamber_temp is not None
    assert math.isnan(detail.chamber_temp)
