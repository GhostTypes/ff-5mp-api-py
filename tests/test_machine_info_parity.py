"""Parity tests for MachineInfo transformation behavior."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta

from flashforge.api.controls.info import MachineInfoParser
from flashforge.models import FFPrinterDetail
from flashforge.models.responses import DetailResponse
from tests.fixtures.printer_responses import AD5X_INFO_RESPONSE, FIVE_M_PRO_INFO_RESPONSE


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
