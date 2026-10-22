"""Server-authoritative vehicle selector joining broad vPIC-derived seed and curated fitments.

Broad model ranges/engine families are *hints*, not verified VIN/model-year
combinations. A curated chassis/engine row is still market-dependent.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import sys
from typing import Any

from .protocols import protocol_candidates

ROOT = (
    Path(sys._MEIPASS) if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parents[2]
)
GLOBAL = ROOT / "data" / "vehicle_catalog.json"
FITMENTS = ROOT / "data" / "vehicle_fitment_catalog.json"


@lru_cache(maxsize=1)
def _load() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        json.loads(GLOBAL.read_text(encoding="utf-8")),
        json.loads(FITMENTS.read_text(encoding="utf-8")),
    )


def _matches(expected: str | None, actual: str | None) -> bool:
    return expected is None or str(expected).strip().casefold() == str(actual or "").strip().casefold()


def _in_ranges(year: int | None, ranges: list[list[int]]) -> bool:
    return year is None or any(int(a) <= year <= int(b) for a, b in ranges)


def _model_record(make: str, item: dict) -> dict[str, Any]:
    return {
        "make": make,
        "model": item["model"],
        "year_ranges": item.get("year_ranges", []),
        "vehicle_type": item.get("vehicle_type", "passenger"),
        "fuel_options": item.get("common_fuels", []),
        "engine_families": item.get("engine_families", []),
        "engine_scope": "broad_family_hint",
        "fitment_verified": False,
        "source": "project-vpic-curated-model-seed",
    }


def list_global_models(
    *, make: str | None = None, model: str | None = None,
    year: int | None = None, limit: int = 500, offset: int = 0,
) -> dict[str, Any]:
    if not 1 <= limit <= 500 or offset < 0:
        raise ValueError("limit must be 1..500 and offset >= 0")
    broad, _ = _load()
    rows = [
        _model_record(m["make"], item)
        for m in broad["makes"] for item in m.get("models", [])
        if _matches(make, m["make"])
        and _matches(model, item["model"])
        and _in_ranges(year, item.get("year_ranges", []))
    ]
    rows.sort(key=lambda x: (x["make"].casefold(), x["model"].casefold()))
    return {
        "total": len(rows),
        "offset": offset,
        "limit": limit,
        "vehicles": rows[offset: offset + limit],
        "metadata": {
            "catalog_type": "broad_make_model",
            "source": broad.get("source", {}),
            "requires_vin_ecu_confirmation": True,
        },
    }


def list_curated_variants(
    *, make: str | None = None, model: str | None = None,
    chassis: str | None = None, year: int | None = None,
    engine: str | None = None, fuel: str | None = None,
    limit: int = 500, offset: int = 0,
) -> dict[str, Any]:
    """Chassis/engine/year fitments are selector hints, never protocol claims."""
    if not 1 <= limit <= 500 or offset < 0:
        raise ValueError("limit must be 1..500 and offset >= 0")
    _, seed = _load()
    result = []
    for v in seed.get("entries", []):
        if not (
            _matches(make, v["make"])
            and _matches(model, v["model"])
            and _matches(chassis, v.get("chassis"))
            and _in_ranges(year, v.get("year_ranges", []))
        ):
            continue
        for e in v.get("engines", []):
            if not _matches(engine, e["name"]):
                continue
            fuels = e.get("fuel", [])
            if fuel is not None and not any(_matches(fuel, choice) for choice in fuels):
                continue
            result.append({
                "make": v["make"],
                "model": v["model"],
                "chassis": v.get("chassis"),
                "year_ranges": v["year_ranges"],
                "engine": e["name"],
                "engine_type": fuels,
                "ecu_hints": e.get("ecus", []),
                "scope": "curated_engine_fitment_hint",
                "vin_verified": False,
                "obd_protocol_confirmed": False,
                "source": seed.get("source", "project-curated-seed"),
            })
    result.sort(key=lambda x: (x["make"], x["model"], x["chassis"] or "", x["engine"]))
    return {
        "total": len(result),
        "limit": limit,
        "offset": offset,
        "variants": result[offset: offset + limit],
        "metadata": {"requires_vin_ecu_confirmation": True, "source": seed.get("source")},
    }


def resolve_vehicle_protocols(
    *, make: str, model: str, year: int | None,
    chassis: str | None = None, engine: str | None = None,
    market: str | None = None, adapter_report: str | None = None,
) -> dict[str, Any]:
    """Candidate protocols + optional adapter observed code. No unsupported VIN assumption."""
    from .protocols import parse_elm_protocol
    global_matches = list_global_models(make=make, model=model, year=year)["vehicles"]
    curated = list_curated_variants(
        make=make, model=model, chassis=chassis, year=year, engine=engine
    )
    vehicle_type = global_matches[0].get("vehicle_type", "passenger") if global_matches else "unknown"
    hints = protocol_candidates(year=year, vehicle_type=vehicle_type, region=market)
    observation = parse_elm_protocol(adapter_report) if adapter_report else None
    return {
        "vehicle": {"make": make, "model": model, "chassis": chassis, "year": year, "engine": engine, "market": market},
        "catalog_model_found": bool(global_matches),
        "curated_variants_found": curated["total"],
        "protocol_hints": hints,
        "adapter_observation": observation,
        "reported_protocol_id": (
            observation["protocol"]["id"] if observation and observation["detected"] else None
        ),
        "observation_provenance": (
            "caller_supplied_ATDPN_not_device_attested" if observation else None
        ),
        "warning": (
            "Adapter protocol only identifies the connected diagnostic link. "
            "It does not prove VIN-specific fitment or support for OEM-specific ECU services."
        ),
    }
