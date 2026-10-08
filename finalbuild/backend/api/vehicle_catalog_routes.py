from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from diagnostic.db_models import VehicleCatalogEntryRow


router = APIRouter(prefix="/api/v1/vehicle-catalog", tags=["vehicle-catalog"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://diagnostic:diagnostic@localhost:5432/diagnostic",
)
_engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)


class CatalogEntry(BaseModel):
    make: str
    model: str
    chassis: str | None = None
    year: int
    engine: str
    ecu: str | None = None
    fuel: list[str] = Field(default_factory=list)
    source: str
    scope: str


def _ensure_catalog_table() -> None:
    VehicleCatalogEntryRow.__table__.create(_engine, checkfirst=True)


def _run_all(sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        _ensure_catalog_table()
        with _engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(sql), params).mappings().all()]
    except Exception as exc:
        raise HTTPException(503, f"Vehicle catalog database unavailable: {exc}") from exc


def _require_make_model(make: str, model: str) -> None:
    if not make.strip() or not model.strip():
        raise HTTPException(400, "make and model are required")




@router.get("/entries", response_model=list[CatalogEntry])
def list_entries(
    make: str | None = None,
    model: str | None = None,
    chassis: str | None = None,
    year: int | None = None,
    engine: str | None = None,
    ecu: str | None = None,
) -> list[CatalogEntry]:
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    for key, value in (
        ("make", make),
        ("model", model),
        ("chassis", chassis),
        ("year", year),
        ("engine", engine),
        ("ecu", ecu),
    ):
        if value is not None and str(value).strip():
            clauses.append(f"{key} = :{key}")
            params[key] = value
    where_clause = " AND ".join(clauses)
    return _run_all(
        f"""
        SELECT make, model, chassis, year, engine, ecu, fuel, source, scope
        FROM vehicle_catalog_entries
        WHERE {where_clause}
        ORDER BY make, model, chassis NULLS LAST, year DESC, engine, ecu NULLS LAST
        """,
        params,
    )
@router.get("/makes", response_model=list[str])
def list_makes() -> list[str]:
    rows = _run_all(
        "SELECT DISTINCT make FROM vehicle_catalog_entries ORDER BY make",
        {},
    )
    return [row["make"] for row in rows]


@router.get("/models", response_model=list[str])
def list_models(make: str = Query(..., min_length=1)) -> list[str]:
    rows = _run_all(
        """
        SELECT DISTINCT model
        FROM vehicle_catalog_entries
        WHERE make = :make
        ORDER BY model
        """,
        {"make": make},
    )
    return [row["model"] for row in rows]


@router.get("/chassis", response_model=list[str])
def list_chassis(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
) -> list[str]:
    _require_make_model(make, model)
    rows = _run_all(
        """
        SELECT DISTINCT chassis
        FROM vehicle_catalog_entries
        WHERE make = :make
          AND model = :model
          AND chassis IS NOT NULL
        ORDER BY chassis
        """,
        {"make": make, "model": model},
    )
    return [row["chassis"] for row in rows]


@router.get("/years", response_model=list[int])
def list_years(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    chassis: str | None = None,
) -> list[int]:
    _require_make_model(make, model)
    rows = _run_all(
        """
        SELECT DISTINCT year
        FROM vehicle_catalog_entries
        WHERE make = :make
          AND model = :model
          AND (
                :chassis IS NULL
                OR chassis = :chassis
                OR chassis IS NULL
          )
        ORDER BY year DESC
        """,
        {"make": make, "model": model, "chassis": chassis},
    )
    return [int(row["year"]) for row in rows]


@router.get("/engines", response_model=list[str])
def list_engines(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    year: int | None = None,
    chassis: str | None = None,
) -> list[str]:
    _require_make_model(make, model)
    rows = _run_all(
        """
        WITH exact AS (
            SELECT DISTINCT engine
            FROM vehicle_catalog_entries
            WHERE make = :make
              AND model = :model
              AND (:year IS NULL OR year = :year)
              AND (:chassis IS NULL OR chassis = :chassis)
              AND chassis IS NOT NULL
              AND scope = 'curated-fitment'
        ),
        broad AS (
            SELECT DISTINCT engine
            FROM vehicle_catalog_entries
            WHERE make = :make
              AND model = :model
              AND (:year IS NULL OR year = :year)
              AND (:chassis IS NULL OR chassis IS NULL)
        )
        SELECT engine FROM exact
        UNION ALL
        SELECT engine FROM broad
        WHERE NOT EXISTS (SELECT 1 FROM exact)
        ORDER BY engine
        """,
        {"make": make, "model": model, "year": year, "chassis": chassis},
    )
    return [row["engine"] for row in rows]


@router.get("/ecus", response_model=list[str])
def list_ecus(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    engine: str = Query(..., min_length=1),
    year: int | None = None,
    chassis: str | None = None,
) -> list[str]:
    _require_make_model(make, model)
    rows = _run_all(
        """
        SELECT DISTINCT ecu
        FROM vehicle_catalog_entries
        WHERE make = :make
          AND model = :model
          AND engine = :engine
          AND (:year IS NULL OR year = :year)
          AND (:chassis IS NULL OR chassis = :chassis OR chassis IS NULL)
          AND ecu IS NOT NULL
        ORDER BY ecu
        """,
        {"make": make, "model": model, "engine": engine, "year": year, "chassis": chassis},
    )
    return [row["ecu"] for row in rows]


@router.get("/resolve", response_model=list[CatalogEntry])
def resolve_variant(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    year: int = Query(..., ge=1886, le=2100),
    engine: str = Query(..., min_length=1),
    chassis: str | None = None,
    ecu: str | None = None,
) -> list[CatalogEntry]:
    _require_make_model(make, model)
    rows = _run_all(
        """
        SELECT make, model, chassis, year, engine, ecu, fuel, source, scope
        FROM vehicle_catalog_entries
        WHERE make = :make
          AND model = :model
          AND year = :year
          AND engine = :engine
          AND (:chassis IS NULL OR chassis = :chassis)
          AND (:ecu IS NULL OR ecu = :ecu)
        ORDER BY
            CASE WHEN scope = 'curated-fitment' THEN 0 ELSE 1 END,
            chassis NULLS LAST,
            ecu NULLS LAST
        """,
        {"make": make, "model": model, "year": year, "engine": engine, "chassis": chassis, "ecu": ecu},
    )
    return rows
