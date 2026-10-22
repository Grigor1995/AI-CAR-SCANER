"""Optional online US NHTSA vPIC make/model/year lookup.

vPIC is a US regulatory dataset; it does not guarantee all makes worldwide or
a VIN-level engine fitment. No automatic VIN transmission to a third party.
"""
from __future__ import annotations

from functools import lru_cache
import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen


@lru_cache(maxsize=128)
def nhtsa_models_for_make_year(make: str, year: int) -> dict:
    if not 1886 <= year <= 2100:
        raise ValueError("year must be 1886..2100")
    if not (1 <= len(make.strip()) <= 80) or "/" in make or "\\" in make:
        raise ValueError("invalid make")
    url = (
        "https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/"
        f"make/{quote(make.strip(), safe='')}/modelyear/{year}?format=json"
    )
    request = Request(url, headers={"User-Agent": "AI-CAR-SCANER/0.6 (NHTSA public vehicle model research)"})
    with urlopen(request, timeout=8) as response:
        payload = json.loads(response.read(2_000_000).decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("Results"), list):
        raise ValueError("invalid vPIC response")
    models = sorted({
        str(row["Model_Name"]).strip()
        for row in payload["Results"]
        if isinstance(row, dict) and row.get("Model_Name")
    })
    return {
        "make": make.strip(),
        "year": year,
        "models": models,
        "count": len(models),
        "source": "US NHTSA vPIC",
        "source_url": url,
        "engine_details": "not_provided_by_this_endpoint",
        "global_market_coverage": False,
        "vin_verified": False,
    }


def nhtsa_decode_vin(vin: str, *, consent_to_nhtsa_lookup: bool) -> dict:
    """Opt-in VIN decoding. VIN is never cached, persisted, or silently queried.

    NHTSA's model/engine result is manufacturer-submitted US-market VIN data,
    not an authoritative engine/ECU match for every national market.
    """
    normalized = vin.strip().upper()
    if not consent_to_nhtsa_lookup:
        raise PermissionError("Explicit consent is required to send a VIN to NHTSA.")
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", normalized):
        raise ValueError("VIN must contain 17 valid characters (I, O and Q are not permitted).")
    url = (
        "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/"
        + quote(normalized, safe="") + "?format=json"
    )
    request = Request(
        url, headers={"User-Agent": "AI-CAR-SCANER/0.6 (consented VIN decoder)"},
    )
    with urlopen(request, timeout=8) as response:
        payload = json.loads(response.read(500_000).decode("utf-8"))
    results = payload.get("Results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise ValueError("invalid NHTSA VIN response")
    result = results[0]
    keys = (
        "Make", "Model", "ModelYear", "VehicleType", "EngineModel",
        "EngineCylinders", "DisplacementL", "FuelTypePrimary",
        "FuelTypeSecondary", "EngineConfiguration", "EngineManufacturer",
        "ErrorCode", "ErrorText",
    )
    values = {key: result.get(key) for key in keys}
    return {
        "source": "US NHTSA vPIC",
        "scope": "us_market_manufacturer_reported_vin_data",
        "vehicle": values,
        "matched_engine_confirmed_by_ecu": False,
        "protocol_confirmed": False,
        "notes": [
            "VIN data was sent to the external NHTSA service with explicit consent.",
            "VIN identity and engine data may be incomplete for non-US vehicles.",
            "The ECU communication protocol must still be detected from the adapter.",
        ],
    }
