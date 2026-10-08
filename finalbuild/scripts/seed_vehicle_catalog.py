from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
CATALOG_FILE = ROOT / "data" / "vehicle_catalog.json"
FITMENTS_FILE = ROOT / "data" / "vehicle_fitments.json"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://diagnostic:diagnostic@localhost:5432/diagnostic",
)


def stable_id(*parts: object):
    return uuid5(NAMESPACE_URL, "ai-car-scaner:vehicle-catalog:" + "|".join(str(x) for x in parts))


def expand_catalog(data: dict) -> list[dict]:
    rows: list[dict] = []
    source_name = str((data.get("source") or {}).get("name") or "canonical-json")
    for make in data.get("makes", []):
        make_name = str(make.get("make", "")).strip()
        for model in make.get("models", []):
            model_name = str(model.get("model", "")).strip()
            year_ranges = model.get("year_ranges", [])
            engines = [str(x).strip() for x in model.get("engine_families", []) if str(x).strip()]
            scope = str(model.get("engine_data_scope") or "family-level")
            for year_range in year_ranges:
                if not isinstance(year_range, list) or len(year_range) != 2:
                    continue
                start, end = int(year_range[0]), int(year_range[1])
                for year in range(min(start, end), max(start, end) + 1):
                    for engine in engines or ["unknown"]:
                        key = (make_name, model_name, None, year, engine, None)
                        rows.append(
                            {
                                "id": stable_id(*key),
                                "make": make_name,
                                "model": model_name,
                                "chassis": None,
                                "year": year,
                                "engine": engine,
                                "ecu": None,
                                "fuel": json.dumps(model.get("common_fuels") or []),
                                "source": source_name,
                                "scope": scope,
                                "metadata": json.dumps(
                                    {
                                        "vehicle_type": model.get("vehicle_type"),
                                        "notes": model.get("notes"),
                                        "engine_market_note": model.get("engine_market_note"),
                                    }
                                ),
                            }
                        )
    return rows


def expand_fitments(data: dict) -> list[dict]:
    rows: list[dict] = []
    for entry in data.get("entries", []):
        make = str(entry.get("make", "")).strip()
        model = str(entry.get("model", "")).strip()
        chassis = str(entry.get("chassis", "")).strip() or None
        for year in entry.get("years", []):
            for engine_data in entry.get("engines", []):
                engine = str(engine_data.get("name", "")).strip()
                for ecu in engine_data.get("ecus", []) or [None]:
                    ecu_value = str(ecu).strip() if ecu is not None else None
                    key = (make, model, chassis, int(year), engine, ecu_value)
                    rows.append(
                        {
                            "id": stable_id(*key),
                            "make": make,
                            "model": model,
                            "chassis": chassis,
                            "year": int(year),
                            "engine": engine,
                            "ecu": ecu_value,
                            "fuel": json.dumps([]),
                            "source": "vehicle_fitments.json",
                            "scope": "curated-fitment",
                            "metadata": json.dumps(
                                {
                                    "fitment_note": "Curated selector hint; exact vehicle fitment still requires VIN/ECU identification.",
                                }
                            ),
                        }
                    )
    return rows


def seed() -> None:
    catalog = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    fitments = json.loads(FITMENTS_FILE.read_text(encoding="utf-8"))
    rows = expand_catalog(catalog) + expand_fitments(fitments)

    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS vehicle_catalog_entries (
                    id UUID PRIMARY KEY,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    chassis TEXT,
                    year INT NOT NULL,
                    engine TEXT NOT NULL,
                    ecu TEXT,
                    fuel JSONB NOT NULL DEFAULT '[]'::jsonb,
                    source TEXT NOT NULL DEFAULT 'unknown',
                    scope TEXT NOT NULL DEFAULT 'family-level',
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    UNIQUE (make, model, chassis, year, engine, ecu)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_make ON vehicle_catalog_entries(make)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_make_model ON vehicle_catalog_entries(make, model)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_model_chassis ON vehicle_catalog_entries(make, model, chassis)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_year ON vehicle_catalog_entries(make, model, chassis, year)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_engine ON vehicle_catalog_entries(make, model, chassis, year, engine)"))

        conn.execute(
            text(
                """
                INSERT INTO vehicle_catalog_entries
                    (id, make, model, chassis, year, engine, ecu, fuel, source, scope, metadata)
                VALUES
                    (:id, :make, :model, :chassis, :year, :engine, :ecu,
                     CAST(:fuel AS jsonb), :source, :scope, CAST(:metadata AS jsonb))
                ON CONFLICT (make, model, chassis, year, engine, ecu)
                DO UPDATE SET
                    fuel = EXCLUDED.fuel,
                    source = EXCLUDED.source,
                    scope = EXCLUDED.scope,
                    metadata = EXCLUDED.metadata
                """
            ),
            rows,
        )

    exact_count = sum(1 for row in rows if row["scope"] == "curated-fitment")
    print(f"Seeded/updated {len(rows)} catalog rows ({exact_count} curated fitment rows).")


if __name__ == "__main__":
    seed()
