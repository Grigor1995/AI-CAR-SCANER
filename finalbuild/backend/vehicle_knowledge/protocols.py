"""Road-vehicle diagnostic protocols: standards, capabilities and cautious hints.

An ELM327/OBD-II transport is not a universal UDS/DoIP/J1939 ECU interface.
All hints are NOT proof that a particular vehicle/ECU implements a protocol.
Never automatically send programming, clearing, or security-access commands.
References: elmelectronics.com/products/ics/obd/; SAE J1979-2;
ISO 14229-1, ISO 13400-2; Softing automotive protocol overview.
"""
from __future__ import annotations

import re
from typing import Any

SOURCES = {
    "elm327": "https://elmelectronics.com/products/ics/obd/",
    "sae_obdonuds": "https://saemobilus.sae.org/standards/j1979-2_202104-e-e-diagnostic-test-modes-obdonuds",
    "uds": "https://automotive.softing.com/standards/protocols.html",
    "obd_manual": "https://www.snapon.com/DiagnosticsManuals/Help/OBDII/Content/Common/Help%20Topics/OBD/Protocol%20Selection.htm",
}

# ELM chip IDs 1-9 and A; physical CAN format matters for selecting a mode.
# Keep protocol names, standardized service family and implementation distinct.
OBD_PROTOCOLS: tuple[dict[str, Any], ...] = (
    {"id": "sae_j1850_pwm", "label": "SAE J1850 PWM", "family": "generic_obd_ii", "elm_id": "1", "supported_by_generic_elm": True},
    {"id": "sae_j1850_vpw", "label": "SAE J1850 VPW", "family": "generic_obd_ii", "elm_id": "2", "supported_by_generic_elm": True},
    {"id": "iso_9141_2", "label": "ISO 9141-2 K-Line", "family": "generic_obd_ii", "elm_id": "3", "supported_by_generic_elm": True},
    {"id": "iso_14230_4_slow", "label": "ISO 14230-4 KWP2000 5-baud", "family": "generic_obd_ii", "elm_id": "4", "supported_by_generic_elm": True},
    {"id": "iso_14230_4_fast", "label": "ISO 14230-4 KWP2000 fast init", "family": "generic_obd_ii", "elm_id": "5", "supported_by_generic_elm": True},
    {"id": "iso_15765_4_11_500", "label": "ISO 15765-4 CAN 11-bit / 500 kbit/s", "family": "generic_obd_ii", "elm_id": "6", "supported_by_generic_elm": True},
    {"id": "iso_15765_4_29_500", "label": "ISO 15765-4 CAN 29-bit / 500 kbit/s", "family": "generic_obd_ii", "elm_id": "7", "supported_by_generic_elm": True},
    {"id": "iso_15765_4_11_250", "label": "ISO 15765-4 CAN 11-bit / 250 kbit/s", "family": "generic_obd_ii", "elm_id": "8", "supported_by_generic_elm": True},
    {"id": "iso_15765_4_29_250", "label": "ISO 15765-4 CAN 29-bit / 250 kbit/s", "family": "generic_obd_ii", "elm_id": "9", "supported_by_generic_elm": True},
    {"id": "sae_j1939_250", "label": "SAE J1939 29-bit CAN / 250 kbit/s", "family": "heavy_duty", "elm_id": "A", "supported_by_generic_elm": False},
    {"id": "sae_j1939_500", "label": "SAE J1939 29-bit CAN / 500 kbit/s", "family": "heavy_duty", "elm_id": None, "supported_by_generic_elm": False},
    {"id": "iso_14229_uds_can", "label": "ISO 14229 UDS over ISO 15765-2 (DoCAN)", "family": "enhanced_ecu", "elm_id": None, "supported_by_generic_elm": False},
    {"id": "iso_14229_uds_doip", "label": "UDS over ISO 13400 Diagnostics over IP", "family": "enhanced_ecu", "elm_id": None, "supported_by_generic_elm": False},
    {"id": "iso_27145_wwh_obd", "label": "ISO 27145 WWH-OBD", "family": "heavy_duty", "elm_id": None, "supported_by_generic_elm": False},
    {"id": "sae_j1979_2_obdonuds", "label": "SAE J1979-2 OBDonUDS", "family": "emissions_service", "elm_id": None, "supported_by_generic_elm": False},
    {"id": "iso_14230_kwp_on_can", "label": "KWP2000 on CAN (manufacturer diagnostics)", "family": "enhanced_ecu", "elm_id": None, "supported_by_generic_elm": False},
)
_BY_ID = {p["id"]: p for p in OBD_PROTOCOLS}
_BY_ELM = {p["elm_id"]: p for p in OBD_PROTOCOLS if p["elm_id"] is not None}

# These categories are suggestions for discovery, not model-specific assertions.
_CAN = ("iso_15765_4_11_500", "iso_15765_4_29_500", "iso_15765_4_11_250", "iso_15765_4_29_250")
_LEGACY = ("iso_9141_2", "iso_14230_4_fast", "iso_14230_4_slow", "sae_j1850_pwm", "sae_j1850_vpw")


def all_protocols() -> list[dict[str, Any]]:
    result = []
    for p in OBD_PROTOCOLS:
        row = dict(p)
        row["capability"] = (
            "ELM_chip_can_read_generic_obd_if_adapter_connected"
            if p["supported_by_generic_elm"]
            else "requires_separate_hardware_and_implementation"
        )
        row["server_hardware_integration"] = "VCI_manager_simulator_only_pending_physical_driver"
        row["source"] = SOURCES["elm327"] if p["elm_id"] else SOURCES["uds"]
        result.append(row)
    return result


def protocol_candidates(
    *, year: int | None, vehicle_type: str = "passenger", region: str | None = None,
) -> dict[str, Any]:
    """No guess can replace an ECU handshake; year/region only changes priority."""
    heavy = vehicle_type.strip().lower() in {"heavy_truck", "heavy-duty", "heavy_duty", "bus", "commercial_heavy"}
    if heavy:
        candidates = ["sae_j1939_250", "sae_j1939_500", "iso_27145_wwh_obd", *_CAN]
    elif year is None:
        candidates = [*_CAN, *_LEGACY]
    elif year >= 2008:
        # US model-year 2008+ emissions CAN mandate is not a global VIN rule.
        candidates = [*_CAN, *_LEGACY]
    else:
        candidates = [*_LEGACY, *_CAN]
    return {
        "selection": "automatic_detection_required",
        "protocol_confirmed": False,
        "confidence": "unverified_candidate",
        "vehicle_type": vehicle_type,
        "region": region,
        "year": year,
        "candidate_protocol_ids": list(dict.fromkeys(candidates)),
        "manual_selection_recommended": False,
        "notes": [
            "Vehicle make/model/year/engine cannot prove ECU protocol. Auto-detect with a compatible adapter.",
            "OBD emissions protocol differs from manufacturer ECU diagnostics (UDS, DoIP).",
            "CAN became mandatory for US light-duty OBD-II from model year 2008; do not assume the same for all markets.",
            "Probe only supported read-only generic services; never silently perform writes, security access or ECU programming.",
        ],
        "sources": [SOURCES["elm327"], SOURCES["obd_manual"]],
    }


def parse_elm_protocol(raw: str | bytes) -> dict[str, Any]:
    """Parse ELM ATDPN protocol code. 'A6' = auto selected 6; 'A0' undecided."""
    value = raw.decode("ascii", errors="replace") if isinstance(raw, bytes) else str(raw)
    compact = re.sub(r"\s+", "", value).upper().replace(">", "")
    # Discard an echoed AT command (only exact leading echo).
    if compact.startswith("ATDPN"):
        compact = compact[5:]
    if compact.startswith("ATDP"):
        compact = compact[4:]
    # ATDP description text (e.g. ISO 15765-4) must never be parsed
    # as ELM code 4; only ATDPN numeric responses are acceptable.
    match = re.fullmatch(r"A?[0-9A-C]", compact)
    code = match.group(0) if match else ""
    automatic = code.startswith("A") and len(code) == 2
    value_id = code[1:] if automatic else code
    protocol = _BY_ELM.get(value_id)
    return {
        "raw": value.strip(),
        "elm_protocol_code": code or None,
        "auto_selected": automatic,
        "detected": protocol is not None,
        "protocol": dict(protocol) if protocol else None,
        "confidence": "adapter_reported" if protocol else "undetermined",
        "warning": None if protocol else "ELM has not selected a recognized OBD protocol (or the adapter response is invalid).",
    }


def get_protocol(protocol_id: str) -> dict[str, Any] | None:
    p = _BY_ID.get(protocol_id)
    return dict(p) if p else None
