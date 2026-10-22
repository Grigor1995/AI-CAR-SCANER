"""Authoritative BACKEND catalogue of standards; not an assertion of hardware support.

Transport (CAN/K-Line/Ethernet), diagnostics (UDS/OBD/J1939), and adapter
capability are separate. Vehicle make/model never confirms a protocol.
Only an observed adapter/ECU handshake can provide measured evidence.
No write services, security access, programming or DTC clearing here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Protocol:
    id: str
    standard: str
    layer: str
    family: str
    elm_code: str | None = None
    support: str = "metadata_only"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# "adapter_dependent" only describes a potential wire transport. It does NOT
# mean that our backend can perform physical ECU transactions.
PROTOCOLS: tuple[Protocol, ...] = (
    Protocol("j1850_pwm", "SAE J1850 PWM", "obd_transport", "J1850", "1", "adapter_dependent", "Older North-American Ford-family applications; auto-detect first."),
    Protocol("j1850_vpw", "SAE J1850 VPW", "obd_transport", "J1850", "2", "adapter_dependent", "Older North-American GM-family applications; auto-detect first."),
    Protocol("iso9141_2", "ISO 9141-2 K-Line", "obd_transport", "K-Line", "3", "adapter_dependent", "K-Line, 5-baud init; older European/Asian OBD."),
    Protocol("iso14230_4_slow", "ISO 14230-4 KWP2000 (5-baud)", "obd_transport", "K-Line", "4", "adapter_dependent", "Legacy emissions OBD over K-Line."),
    Protocol("iso14230_4_fast", "ISO 14230-4 KWP2000 (fast init)", "obd_transport", "K-Line", "5", "adapter_dependent", "Legacy emissions OBD over K-Line."),
    Protocol("iso15765_4_can11_500", "ISO 15765-4 CAN 11-bit / 500 kbit/s", "obd_transport", "CAN", "6", "adapter_dependent", "Common passenger-vehicle CAN OBD."),
    Protocol("iso15765_4_can29_500", "ISO 15765-4 CAN 29-bit / 500 kbit/s", "obd_transport", "CAN", "7", "adapter_dependent", "Extended-address CAN OBD."),
    Protocol("iso15765_4_can11_250", "ISO 15765-4 CAN 11-bit / 250 kbit/s", "obd_transport", "CAN", "8", "adapter_dependent", "Not universally supported by adapters or vehicles."),
    Protocol("iso15765_4_can29_250", "ISO 15765-4 CAN 29-bit / 250 kbit/s", "obd_transport", "CAN", "9", "adapter_dependent", "Not universally supported by adapters or vehicles."),
    Protocol("j1939_250", "SAE J1939-73 29-bit / 250 kbit/s", "commercial_obd", "J1939", "A", "adapter_dependent", "Heavy-duty vehicles; SPN/FMI, not generic passenger-car PID semantics."),
    Protocol("j1939_500", "SAE J1939 / 500 kbit/s", "commercial_obd", "J1939", None, "metadata_only", "Support requires J1939-capable device and implementation."),
    Protocol("uds_on_can", "ISO 14229-1 UDS on ISO 15765-2 DoCAN", "diagnostic_application", "UDS", None, "simulator_only", "Manufacturer-specific ECU addressing/services require separate discovery and authorization."),
    Protocol("uds_on_doip", "ISO 14229 UDS over ISO 13400 DoIP", "diagnostic_application", "DoIP", None, "metadata_only", "Ethernet discovery/routing activation; not an ELM327 ATSP protocol."),
    Protocol("uds_on_can_fd", "UDS over CAN FD", "diagnostic_application", "CAN-FD", None, "metadata_only", "Requires CAN-FD adapter and ECU-specific discovery; not ELM327 classical CAN."),
    Protocol("wwh_obd", "ISO 27145 WWH-OBD", "regulatory_diagnostic", "WWH-OBD", None, "metadata_only", "CAN or DoIP depending on the vehicle; distinct from generic OBD-II Mode 01."),
    Protocol("obdonuds", "SAE J1979-2 OBDonUDS", "regulatory_diagnostic", "OBDonUDS", None, "metadata_only", "Introduction and compliance differ by market/class/model year."),
    Protocol("kwp1281", "VW Group KW1281", "manufacturer_specific", "K-Line", None, "metadata_only", "Not ISO 14230-4 generic OBD; special adapter/software needed."),
    Protocol("single_wire_can", "SAE J2411 Single-Wire CAN / GMLAN", "manufacturer_specific", "SWCAN", None, "metadata_only", "Manufacturer bus outside generic emissions CAN pins."),
    Protocol("lin", "ISO 17987 LIN", "subsystem_bus", "LIN", None, "metadata_only", "Not a generic OBD-II vehicle connection."),
    Protocol("flexray", "ISO 17458 FlexRay / UDSonFR", "subsystem_bus", "FlexRay", None, "metadata_only", "Not a generic OBD-II vehicle connection."),
    Protocol("j1708_j1587", "SAE J1708 / J1587", "commercial_legacy", "J1708", None, "metadata_only", "Legacy heavy-duty network, not supported by classic ELM327."),
)
BY_ID = {p.id: p for p in PROTOCOLS}
BY_ELM_CODE = {p.elm_code: p for p in PROTOCOLS if p.elm_code is not None}

CANDIDATE_NOTICE = (
    "Candidates are regulation/era hints, never confirmed per model or ECU. "
    "Use adapter auto-detect and read-only identification first; cross-check VIN, "
    "region, vehicle class and detected ECU. No physical compatibility is guaranteed."
)


def all_protocols() -> list[dict[str, Any]]:
    return [p.to_dict() for p in PROTOCOLS]


def read_elm_detected_protocol(raw: str) -> dict[str, Any]:
    """Parse an observed ELM327 ATDPN reply: A6/6, A3/3, etc.

    This function does not communicate with hardware or send AT commands.
    No success claim is made from a configured setting without an observation.
    """
    normalized = raw.strip().upper().replace(" ", "").replace("\r", "").replace("\n", "")
    auto_selected = normalized.startswith("A")
    code = normalized[1:] if auto_selected else normalized
    protocol = BY_ELM_CODE.get(code) if len(code) == 1 else None
    return {
        "raw": raw,
        "adapter_observation": "ATDPN",
        "protocol_id": protocol.id if protocol else None,
        "auto_selected": auto_selected,
        "evidence": "adapter_reported" if protocol else "unrecognized",
        "confirmed_ecu_communication": False,
    }


def _add(target: list[str], *items: str) -> None:
    for item in items:
        if item not in target:
            target.append(item)


def assess_protocols(
    *, year: int, market: str = "unknown", make: str = "",
    fuel: str = "", vehicle_class: str = "passenger",
    detected_elm: str | None = None,
) -> dict[str, Any]:
    """Conservative compatibility HINTS, never make/model-to-ECU assertions."""
    market = market.strip().upper()
    vehicle_class = vehicle_class.strip().lower()
    fuel = fuel.strip().lower()
    make = make.strip().lower()
    candidates: list[str] = []
    warnings: list[str] = []
    if year < 1886 or year > 2100:
        raise ValueError("year outside supported range")
    heavy = vehicle_class in {"heavy", "heavy-duty", "truck-heavy", "bus", "commercial-heavy"}
    if heavy:
        _add(candidates, "j1939_250", "j1939_500", "wwh_obd")
        if year >= 2023:
            _add(candidates, "obdonuds")
        warnings.append("Commercial J1939/WWH-OBD depends on engine certification, region and vehicle OEM.")
    elif fuel in {"electric", "battery-electric", "bev", "ev"}:
        _add(candidates, "uds_on_can", "uds_on_doip")
        warnings.append("A BEV may not expose combustion-emissions OBD PIDs; OEM diagnostics are separate.")
    elif market in {"US", "USA", "CA", "CANADA"} and year >= 2008:
        _add(candidates, "iso15765_4_can11_500", "iso15765_4_can29_500")
        if year >= 2023:
            _add(candidates, "obdonuds")
        warnings.append("CAN-based emissions OBD is expected for covered US/Canada passenger model years; CAN ID format must be detected.")
    elif market in {"EU", "EEA", "UK"} and year >= 2008:
        _add(candidates, "iso15765_4_can11_500", "iso15765_4_can29_500",
             "iso15765_4_can11_250", "iso15765_4_can29_250")
        warnings.append("European EOBD and network changes vary by registration, fuel and model year.")
    elif year >= 2008:
        _add(candidates, "iso15765_4_can11_500", "iso15765_4_can29_500",
             "iso15765_4_can11_250", "iso15765_4_can29_250",
             "iso14230_4_fast", "iso9141_2")
        warnings.append("No OBD legal applicability can be assumed for an unspecified market.")
    elif year >= 1996:
        if market in {"US", "USA", "CA", "CANADA"} and make in {
            "ford", "lincoln", "mercury",
        }:
            _add(candidates, "j1850_pwm")
        elif market in {"US", "USA", "CA", "CANADA"} and make in {
            "chevrolet", "gmc", "buick", "cadillac", "pontiac", "oldsmobile",
        }:
            _add(candidates, "j1850_vpw")
        _add(candidates, "iso9141_2", "iso14230_4_slow", "iso14230_4_fast",
             "j1850_pwm", "j1850_vpw", "iso15765_4_can11_500", "iso15765_4_can29_500")
        warnings.append("1996–2007 OBD interfaces may use J1850, K-Line or CAN; manufacturer is only a weak heuristic.")
    else:
        _add(candidates, "iso9141_2", "iso14230_4_slow", "j1850_pwm", "j1850_vpw")
        warnings.append("Pre-1996 standardized 16-pin OBD-II is not assured; inspect OEM diagnostic equipment.")
    detected = read_elm_detected_protocol(detected_elm) if detected_elm is not None else None
    return {
        "year": year, "market": market.lower(), "vehicle_class": vehicle_class,
        "fuel": fuel, "make": make,
        "detection_command": "ATSP0",  # ELM auto mode (not a scan executed by this API).
        "readback_command": "ATDPN",
        "candidates": [
            {"id": id, "standard": BY_ID[id].standard, "support": BY_ID[id].support}
            for id in candidates
        ],
        "detected": detected,
        "confidence": "adapter_reported" if detected and detected["protocol_id"] else "unverified_hint",
        "evidence_source": "market/year/class heuristic; adapter readback if supplied",
        "warnings": warnings,
        "notice": CANDIDATE_NOTICE,
    }
