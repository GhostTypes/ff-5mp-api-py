"""Parity tests for MachineInfo transformation behavior."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta

from flashforge.api.controls.info import MachineInfoParser
from flashforge.client import FiveMClientConnectionOptions, FlashForgeClient
from flashforge.models import FFPrinterDetail
from flashforge.models.responses import DetailResponse
from tests.fixtures.printer_responses import (
    AD5X_INFO_RESPONSE,
    CREATOR_5_INFO_RESPONSE,
    CREATOR_5_PRO_INFO_RESPONSE,
    CREATOR_5_PRO_MATL_STATION_INFO,
    FIVE_M_PRO_INFO_RESPONSE,
)


def _parse_detail(payload: dict):
    detail = DetailResponse(**payload).detail
    machine_info = MachineInfoParser.from_detail(detail)
    assert machine_info is not None
    return machine_info


def test_machine_info_detects_ad5x_from_material_station_with_custom_name():
    """Material-station capability determines AD5X even when the printer is renamed."""
    payload = deepcopy(AD5X_INFO_RESPONSE)
    payload["detail"]["name"] = "Workshop Printer"

    machine_info = _parse_detail(payload)

    assert machine_info.name == "Workshop Printer"
    assert machine_info.is_ad5x is True
    assert machine_info.is_pro is False
    assert machine_info.has_matl_station is True
    assert machine_info.matl_station_info is not None
    assert machine_info.matl_station_info.slot_cnt == 4


def test_machine_info_parses_non_ad5x_pro_models():
    """5M Pro remains a Pro model and not an AD5X."""
    machine_info = _parse_detail(FIVE_M_PRO_INFO_RESPONSE)

    assert machine_info.name == "Adventurer 5M Pro"
    assert machine_info.is_ad5x is False
    assert machine_info.is_pro is True


def test_machine_info_sets_completion_time_and_progress_fields():
    """ETA, completion time, and integer progress mirror the TS library behavior."""
    before = datetime.now()
    machine_info = _parse_detail(AD5X_INFO_RESPONSE)
    after = datetime.now()

    assert machine_info.print_eta == "01:00"
    assert machine_info.print_progress == 0.25
    assert machine_info.print_progress_int == 25
    assert before + timedelta(seconds=3590) <= machine_info.completion_time <= after + timedelta(
        seconds=3610
    )


def test_machine_info_detects_ad5x_from_pid_when_renamed_without_matl_station():
    """PID-based detection identifies AD5X even when renamed and matl_station fields are absent.

    Regression test for ff-5mp-hass#13: a user renamed their printer and the
    name+capability fallback could no longer recognize the model. The
    firmware-set integer pid is stable across renames.
    """
    payload = deepcopy(AD5X_INFO_RESPONSE)
    payload["detail"]["name"] = "LegoTech82"
    payload["detail"]["pid"] = 38
    payload["detail"].pop("hasMatlStation", None)
    payload["detail"].pop("matlStationInfo", None)

    machine_info = _parse_detail(payload)

    assert machine_info.name == "LegoTech82"
    assert machine_info.pid == 38
    assert machine_info.is_ad5x is True
    assert machine_info.is_pro is False


def test_machine_info_detects_5m_pro_from_pid_when_renamed():
    """PID 36 marks the printer as a 5M Pro regardless of the user-set name."""
    payload = deepcopy(FIVE_M_PRO_INFO_RESPONSE)
    payload["detail"]["name"] = "MyPrinter"
    payload["detail"]["pid"] = 36

    machine_info = _parse_detail(payload)

    assert machine_info.name == "MyPrinter"
    assert machine_info.pid == 36
    assert machine_info.is_pro is True
    assert machine_info.is_ad5x is False


def test_machine_info_detects_plain_5m_from_pid():
    """PID 35 is a plain Adventurer 5M; both capability flags are False."""
    payload = deepcopy(FIVE_M_PRO_INFO_RESPONSE)
    payload["detail"]["name"] = "Adventurer 5M Pro"  # name suggests Pro, pid says otherwise
    payload["detail"]["pid"] = 35

    machine_info = _parse_detail(payload)

    assert machine_info.pid == 35
    assert machine_info.is_pro is False
    assert machine_info.is_ad5x is False


def test_machine_info_falls_back_to_name_when_pid_absent():
    """Legacy firmware without a pid field still works via the name+capability fallback."""
    payload = deepcopy(AD5X_INFO_RESPONSE)
    payload["detail"].pop("pid", None)

    machine_info = _parse_detail(payload)

    assert machine_info.pid is None
    assert machine_info.is_ad5x is True  # detected via has_matl_station
    assert machine_info.is_pro is False


def test_machine_info_handles_minimal_detail_defaults():
    """Missing optional fields should still produce a valid machine info object."""
    detail = FFPrinterDetail(name="Minimal")
    machine_info = MachineInfoParser.from_detail(detail)

    assert machine_info is not None
    assert machine_info.name == "Minimal"
    assert machine_info.pid is None
    assert machine_info.is_ad5x is False
    assert machine_info.is_pro is False
    assert machine_info.firmware_version == ""
    assert machine_info.cooling_fan_speed == 0
    assert machine_info.print_bed.current == 0
    assert machine_info.extruder.set == 0


# ---------------------------------------------------------------------------
# Creator 5 / Creator 5 Pro
# ---------------------------------------------------------------------------


def test_machine_info_detects_creator5_pro_from_pid():
    """PID 41 marks the printer as both Creator 5 and Creator 5 Pro."""
    machine_info = _parse_detail(CREATOR_5_PRO_INFO_RESPONSE)

    assert machine_info.pid == 41
    assert machine_info.is_creator5 is True
    assert machine_info.is_creator5_pro is True
    # A Creator 5 Pro must NOT be mis-classified as a 5M Pro despite "Pro".
    assert machine_info.is_pro is False
    assert machine_info.is_ad5x is False


def test_machine_info_detects_creator5_from_pid():
    """PID 40 is a plain Creator 5 (not the Pro variant)."""
    machine_info = _parse_detail(CREATOR_5_INFO_RESPONSE)

    assert machine_info.pid == 40
    assert machine_info.is_creator5 is True
    assert machine_info.is_creator5_pro is False
    assert machine_info.is_pro is False
    assert machine_info.is_ad5x is False


def test_machine_info_parses_creator5_per_tool_temperatures():
    """Creator 5 reports one temperature pair per nozzle in tool_temps."""
    machine_info = _parse_detail(CREATOR_5_PRO_INFO_RESPONSE)

    assert machine_info.nozzle_count == 4
    assert len(machine_info.tool_temps) == 4
    assert (machine_info.tool_temps[2].current, machine_info.tool_temps[2].set) == (205.0, 210.0)
    # The first tool mirrors `extruder` for single-tool API compatibility.
    assert machine_info.extruder.current == 195.0
    assert machine_info.chamber is not None
    assert (machine_info.chamber.current, machine_info.chamber.set) == (50.0, 60.0)


def test_machine_info_creator5_capability_flags():
    """Creator 5 capability flags are derived from presence/value fields."""
    machine_info = _parse_detail(CREATOR_5_PRO_INFO_RESPONSE)

    assert machine_info.has_camera is True  # detail.camera == 1
    assert machine_info.has_lidar is True  # detail.lidar == 1
    # Only the Pro variant has a confirmed door sensor.
    assert machine_info.has_door_sensor is True
    assert machine_info.model == "Creator 5 Pro"

    plain = _parse_detail(CREATOR_5_INFO_RESPONSE)
    assert plain.has_door_sensor is False
    assert plain.model == "Creator 5"


def test_machine_info_creator5_pro_door_sensor_when_door_open():
    """Pro variant still reports a real door sensor even when the door is open."""
    payload = deepcopy(CREATOR_5_PRO_INFO_RESPONSE)
    payload["detail"]["doorStatus"] = "open"

    machine_info = _parse_detail(payload)

    assert machine_info.door_open is True
    assert machine_info.has_door_sensor is True


def test_machine_info_detects_creator5_pro_when_renamed_via_pid():
    """A renamed Creator 5 Pro is still detected via its stable pid."""
    payload = deepcopy(CREATOR_5_PRO_INFO_RESPONSE)
    payload["detail"]["name"] = "Studio Rig"
    payload["detail"].pop("model", None)  # force pid-only resolution for `model`

    machine_info = _parse_detail(payload)

    assert machine_info.name == "Studio Rig"
    assert machine_info.is_creator5 is True
    assert machine_info.is_creator5_pro is True
    assert machine_info.is_pro is False  # not a 5M Pro
    # `model` falls back to the PID-derived name when the firmware omits it.
    assert machine_info.model == "Creator 5 Pro"


def test_machine_info_name_fallback_does_not_misclassify_creator5_pro_as_5m_pro():
    """Regression: a 'Creator 5 Pro' name contains 'Pro' but is NOT a 5M Pro.

    Older firmware without a pid must still classify it as the Creator 5 Pro
    family, never as a 5M Pro.
    """
    payload = deepcopy(CREATOR_5_PRO_INFO_RESPONSE)
    payload["detail"].pop("pid", None)  # force the name-based fallback

    machine_info = _parse_detail(payload)

    assert machine_info.pid is None
    assert machine_info.is_creator5 is True
    assert machine_info.is_creator5_pro is True
    assert machine_info.is_pro is False  # the key guard against mis-classification


def test_machine_info_creator5_has_camera_via_stream_url_when_flag_absent():
    """Models that omit the `camera` flag still report a camera via the stream URL."""
    payload = deepcopy(CREATOR_5_INFO_RESPONSE)
    payload["detail"].pop("camera", None)
    payload["detail"]["cameraStreamUrl"] = "http://192.168.1.150/?action=stream"

    machine_info = _parse_detail(payload)

    assert machine_info.has_camera is True


def test_machine_info_derives_material_station_when_the_flag_is_absent():
    """A Creator 5 Pro reports a station but never the `hasMatlStation` flag.

    Regression test: `has_matl_station` used to be a straight copy of the raw
    field, so it stayed None on the Creator 5 series and every consumer gating
    on it concluded there was no station - while matlStationInfo listed four
    loaded slots. Verified against real hardware (pid 41, firmware 1.9.4).
    """
    payload = deepcopy(CREATOR_5_PRO_INFO_RESPONSE)
    payload["detail"]["matlStationInfo"] = deepcopy(CREATOR_5_PRO_MATL_STATION_INFO)
    assert "hasMatlStation" not in payload["detail"]  # exactly what the printer sends

    machine_info = _parse_detail(payload)

    # The raw model still carries the firmware's (absent) value...
    detail = DetailResponse(**payload).detail
    assert detail.has_matl_station is None
    # ...while the parsed capability reflects what the slots prove.
    assert machine_info.has_matl_station is True
    assert machine_info.matl_station_info is not None
    assert machine_info.matl_station_info.slot_cnt == 4
    assert [slot.material_name for slot in machine_info.matl_station_info.slot_infos] == [
        "PLA",
        "PETG",
        "PLA",
        "PLA",
    ]
    # Deriving the station must not drag a Creator 5 into AD5X detection.
    assert machine_info.is_ad5x is False
    assert machine_info.is_creator5_pro is True


def test_machine_info_material_station_is_false_not_none_when_absent():
    """No flag and no station block reports False - the capability has no unknown state.

    A None here is what let consumers read "not reported" as "no hardware"; the
    parser always resolves the question it was asked.
    """
    machine_info = _parse_detail(CREATOR_5_PRO_INFO_RESPONSE)

    assert machine_info.matl_station_info is None
    assert machine_info.has_matl_station is False


def test_machine_info_material_station_false_when_flag_says_so_without_slots():
    """A model that explicitly reports no station keeps reporting none."""
    machine_info = _parse_detail(FIVE_M_PRO_INFO_RESPONSE)

    assert machine_info.has_matl_station is False


def test_machine_info_creator5_single_nozzle_falls_back_to_extruder():
    """If nozzle arrays are absent, tool_temps mirrors the main extruder."""
    payload = deepcopy(CREATOR_5_INFO_RESPONSE)
    payload["detail"].pop("nozzleTemps", None)
    payload["detail"].pop("nozzleTargetTemps", None)
    payload["detail"]["nozzleCnt"] = None

    machine_info = _parse_detail(payload)

    assert len(machine_info.tool_temps) == 1
    assert machine_info.nozzle_count == 1
    assert machine_info.tool_temps[0].current == 200.0


# ---------------------------------------------------------------------------
# http_only / is_creator5 transport selection on the client
# ---------------------------------------------------------------------------


def test_client_http_only_false_by_default_for_modern_printer():
    """A non-Creator-5 printer defaults to TCP-capable (http_only False)."""
    client = FlashForgeClient("192.168.1.10", "SN", "CHECK")

    assert client.is_creator5 is False
    assert client.is_creator5_pro is False
    assert client.http_only is False
    assert client.can_use_tcp() is True


def test_client_http_only_explicit_override():
    """An explicit http_only override is honored regardless of model."""
    client = FlashForgeClient(
        "192.168.1.10", "SN", "CHECK", FiveMClientConnectionOptions(http_only=True)
    )

    assert client.http_only is True
    assert client.can_use_tcp("get_temp") is False

    tcp_client = FlashForgeClient(
        "192.168.1.10", "SN", "CHECK", FiveMClientConnectionOptions(http_only=False)
    )
    assert tcp_client.http_only is False


def test_client_caches_creator5_flags_and_sets_http_only():
    """cache_details propagates Creator 5 detection and enables http_only."""
    from flashforge.api.controls.info import MachineInfoParser
    from flashforge.models.responses import DetailResponse

    detail = DetailResponse(**CREATOR_5_PRO_INFO_RESPONSE).detail
    machine_info = MachineInfoParser.from_detail(detail)
    assert machine_info is not None

    client = FlashForgeClient("192.168.1.10", "SN", "CHECK")
    assert client.http_only is False  # before caching

    assert client.cache_details(machine_info) is True

    assert client.is_creator5 is True
    assert client.is_creator5_pro is True
    assert client.http_only is True  # auto-set from detected model
    assert client.can_use_tcp() is False


def test_client_explicit_override_wins_over_detected_model():
    """An http_only=False override keeps TCP enabled even for a Creator 5."""
    from flashforge.api.controls.info import MachineInfoParser
    from flashforge.models.responses import DetailResponse

    detail = DetailResponse(**CREATOR_5_PRO_INFO_RESPONSE).detail
    machine_info = MachineInfoParser.from_detail(detail)

    client = FlashForgeClient(
        "192.168.1.10", "SN", "CHECK", FiveMClientConnectionOptions(http_only=False)
    )
    client.cache_details(machine_info)

    assert client.is_creator5_pro is True
    assert client.http_only is False  # override wins
    assert client.can_use_tcp() is True


async def test_client_dispose_does_not_touch_tcp_when_http_only():
    """An HTTP-only client must not attempt a TCP connect during dispose.

    The Creator 5 has no TCP/8899 service. If dispose() tried the logout
    handshake it would block for the connect timeout. Verify dispose() returns
    promptly (well under the default 5s TCP timeout) for an http-only client.
    """
    import time

    client = FlashForgeClient(
        "192.168.1.241",  # unroutable-ish address; no TCP listener expected
        "SN",
        "CHECK",
        FiveMClientConnectionOptions(http_only=True),
    )

    start = time.monotonic()
    await client.dispose()  # must not hang on a TCP connect attempt
    elapsed = time.monotonic() - start

    assert client.http_only is True
    assert elapsed < 1.0, f"dispose() took {elapsed:.2f}s, likely attempted a TCP connect"
