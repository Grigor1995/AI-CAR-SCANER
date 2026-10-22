"""Offline contract tests — no hardware, cloud APIs, or CI needed."""
import pytest

from vehicle.protocol.registry import (
    PROTOCOLS, all_protocols, read_elm_detected_protocol, assess_protocols
)


def test_transport_catalog_covers_all_elm_obd_choices_without_claiming_hardware():
    entries = all_protocols()
    assert len(entries) >= 20
    assert len({x["id"] for x in entries}) == len(entries)
    assert {p.elm_code for p in PROTOCOLS if p.elm_code} >= set("123456789A")
    assert all(x["support"] != "hardware_verified" for x in entries)
    assert next(x for x in entries if x["id"] == "uds_on_doip")["elm_code"] is None


@pytest.mark.parametrize("raw, expected, auto", [
    ("A6", "iso15765_4_can11_500", True),
    ("6", "iso15765_4_can11_500", False),
    ("A3", "iso9141_2", True),
    ("A5", "iso14230_4_fast", True),
    ("AA", "j1939_250", True),
])
def test_parse_elm_atdpn_readback(raw, expected, auto):
    result = read_elm_detected_protocol(raw)
    assert result["protocol_id"] == expected
    assert result["auto_selected"] is auto
    assert result["confirmed_ecu_communication"] is False


def test_unknown_adapter_readback_never_invents_support():
    result = read_elm_detected_protocol("SEARCHING")
    assert result["protocol_id"] is None
    assert result["evidence"] == "unrecognized"


def test_us_2008_passenger_prioritizes_can_but_does_not_claim_certainty():
    x = assess_protocols(year=2008, market="US", make="Ford")
    assert x["candidates"][0]["id"] == "iso15765_4_can11_500"
    assert x["confidence"] == "unverified_hint"
    assert "confirmed" in x["notice"].lower()


@pytest.mark.parametrize("make,first", [
    ("Ford", "j1850_pwm"), ("Chevrolet", "j1850_vpw")
])
def test_older_us_manufacturer_is_weak_hint_only(make, first):
    x = assess_protocols(year=2000, market="US", make=make)
    assert x["candidates"][0]["id"] == first
    assert x["confidence"] == "unverified_hint"


def test_europe_2005_is_not_assigned_a_single_protocol():
    x = assess_protocols(year=2005, market="EU", make="Mercedes-Benz")
    assert len(x["candidates"]) > 3
    assert x["detection_command"] == "ATSP0"


def test_battery_electric_vehicle_has_no_fake_emissions_pid_claim():
    x = assess_protocols(year=2022, market="EU", fuel="battery-electric")
    assert x["candidates"][0]["id"] == "uds_on_can"
    assert "emissions" in x["warnings"][0]


def test_heavy_duty_and_obdonuds_are_not_generic_elm_supported():
    x = assess_protocols(year=2027, market="US", vehicle_class="heavy")
    ids = [c["id"] for c in x["candidates"]]
    assert {"j1939_250", "wwh_obd", "obdonuds"} <= set(ids)
    assert next(c for c in x["candidates"] if c["id"] == "obdonuds")["support"] == "metadata_only"


def test_hardware_detected_protocol_is_adapter_report_only():
    x = assess_protocols(year=2006, market="EU", detected_elm="A6")
    assert x["confidence"] == "adapter_reported"
    assert x["detected"]["confirmed_ecu_communication"] is False


@pytest.mark.parametrize("year", [1800, 2200])
def test_year_safety(year):
    with pytest.raises(ValueError):
        assess_protocols(year=year)
