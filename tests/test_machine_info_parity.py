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


def test_machine_info_handles_minimal_detail_defaults():
    """Missing optional fields should still produce a valid machine info object."""
    detail = FFPrinterDetail(name="Minimal")
    machine_info = MachineInfoParser.from_detail(detail)

    assert machine_info is not None
    assert machine_info.name == "Minimal"
    assert machine_info.is_ad5x is False
    assert machine_info.is_pro is False
    assert machine_info.firmware_version == ""
    assert machine_info.cooling_fan_speed == 0
    assert machine_info.print_bed.current == 0
    assert machine_info.extruder.set == 0
