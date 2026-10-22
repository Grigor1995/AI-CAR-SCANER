"""Single backend registry for the project global seed and curated engine fitments.

The NHTSA-derived make/model year ranges are broad, engine_families are hints;
the 22 curated chassis entries have engine labels but are NOT VIN-verified
individual vehicles. All clients must use this API as their authoritative
catalogue, preserving only a clearly labelled offline presentation fallback.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_PATH = ROOT / "data" / "vehicle_catalog.json"
FITMENT_PATH = ROOT / "data" / "vehicle_fitments.json"


@lru_cache(maxsize=1)
def global_catalog() -> dict[str, Any]:
    return json.loads(GLOBAL_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def curated_fitments() -> dict[str, Any]:
    return json.loads(FITMENT_PATH.read_text(encoding="utf-8"))


def makes(query: str = "") -> list[str]:
    needle = query.casefold().strip()
    return sorted({
        entry["make"] for entry in global_catalog()["makes"]
        if needle in entry["make"].casefold()
    })


def models(make: str, year: int | None = None, query: str = "", limit: int = 300) -> list[dict[str, Any]]:
    if not make.strip():
        return []
    result: list[dict[str, Any]] = []
    for brand in global_catalog()["makes"]:
        if brand["make"].casefold() != make.casefold():
            continue
        for row in brand["models"]:
            if query and query.casefold().strip() not in row["model"].casefold():
                continue
            ranges = row.get("year_ranges") or []
            if year is not None and not any(low <= year <= high for low, high in ranges):
                continue
            result.append({
                "make": brand["make"],
                "model": row["model"],
                "year_ranges": ranges,
                "vehicle_type": row.get("vehicle_type"),
                "engine_families": row.get("engine_families", []),
                "common_fuels": row.get("common_fuels", []),
                "engine_scope": row.get("engine_data_scope", "family-level"),
                "source": global_catalog().get("source", {}).get("name", "project-seed"),
                "disclaimer": "Model-family hints only; year-specific engine fitment requires VIN/market confirmation.",
            })
    return sorted(result, key=lambda row: row["model"])[:limit]


def fitments(make: str, model: str, year: int | None = None) -> list[dict[str, Any]]:
    answer: list[dict[str, Any]] = []
    for row in curated_fitments()["entries"]:
        if row["make"].casefold() != make.casefold() or row["model"].casefold() != model.casefold():
            continue
        years = row.get("years", [])
        if year is not None and year not in years:
            continue
        answer.append({
            "make": row["make"], "model": row["model"],
            "chassis": row["chassis"], "years": years if year is None else [year],
            "engines": row.get("engines", []),
            "source": "project-curated-fitment",
            "scope": "selector_hint_not_vin_verified",
            "disclaimer": "Chassis, engine and ECU choices vary by model year, VIN, engine market and option code.",
        })
    return answer


def registry_stats() -> dict[str, Any]:
    brands = global_catalog()["makes"]
    curated = curated_fitments()["entries"]
    return {
        "make_count": len(brands),
        "global_model_families": sum(len(make["models"]) for make in brands),
        "curated_chassis_entries": len(curated),
        "global_source": global_catalog().get("source", {}),
        "worldwide_exhaustive": False,
        "data_authority": "backend",
        "engines": "family-level globally; selected curated chassis hints, not VIN-level certainty",
    }
