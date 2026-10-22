from __future__ import annotations

import os
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from diagnostic.db_models import VehicleCatalogEntryRow
from diagnostic.database import database_engine


router = APIRouter(prefix="/api/v1/vehicle-catalog", tags=["vehicle-catalog"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://diagnostic:diagnostic@localhost:5432/diagnostic",
)
_engine = database_engine(DATABASE_URL)


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
            rows = [dict(row) for row in conn.execute(text(sql), params).mappings().all()]
            # Raw SQL returns SQLite JSON columns as strings; PostgreSQL
            # already decodes them. Preserve the shared list-valued API.
            for row in rows:
                if isinstance(row.get("fuel"), str):
                    row["fuel"] = json.loads(row["fuel"])
            return rows
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


# v2 knowledge endpoints are backend-authoritative and database-independent.
# Existing /entries, /engines and /resolve endpoints remain API compatible.
from pathlib import Path
from urllib.error import HTTPError, URLError
from fastapi.responses import FileResponse

from vehicle_knowledge.catalog import (
    list_global_models as _global_models,
    list_curated_variants as _curated_variants,
    resolve_vehicle_protocols as _resolve_protocols,
)
from vehicle_knowledge.protocols import all_protocols as _protocols
from vehicle_knowledge.images import (
    bundled_image_metadata as _image_info,
    bundled_model_artwork as _artwork,
    search_licensed_commons_photos as _commons_images,
)


@router.get("/global-models")
def global_models(
    make: str | None = None, model: str | None = None,
    year: int | None = Query(default=None, ge=1886, le=2100),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return _global_models(make=make, model=model, year=year, limit=limit, offset=offset)


@router.get("/curated-variants")
def curated_variants(
    make: str | None = None, model: str | None = None,
    chassis: str | None = None,
    year: int | None = Query(default=None, ge=1886, le=2100),
    engine: str | None = None, fuel: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return _curated_variants(
        make=make, model=model, chassis=chassis, year=year, engine=engine,
        fuel=fuel, limit=limit, offset=offset,
    )


@router.get("/obd-protocols")
def obd_protocols():
    return {
        "protocols": _protocols(),
        "caution": "Catalog coverage is not proof of adapter hardware support or an ECU handshake.",
    }


@router.get("/protocol-hints")
def vehicle_protocol_hints(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    year: int | None = Query(default=None, ge=1886, le=2100),
    chassis: str | None = None,
    engine: str | None = None,
    market: str | None = None,
    adapter_report: str | None = Query(default=None, max_length=64),
):
    return _resolve_protocols(
        make=make, model=model, year=year, chassis=chassis, engine=engine,
        market=market, adapter_report=adapter_report,
    )


@router.get("/image-metadata")
def image_metadata(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    chassis: str = Query(..., min_length=1),
):
    return _image_info(make, model, chassis)


@router.get("/artwork")
def model_artwork(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    chassis: str = Query(..., min_length=1),
):
    file = _artwork(make, model, chassis)
    if file is None:
        raise HTTPException(404, "No bundled vehicle portrait for this chassis")
    return FileResponse(
        file,
        media_type="image/png" if file.suffix == ".png" else "image/svg+xml",
        headers={"X-Image-Source": "project-generated-artwork-not-photo"},
    )


@router.get("/commons-photo-candidates")
def commons_photo_candidates(
    make: str = Query(..., min_length=1, max_length=80),
    model: str = Query(..., min_length=1, max_length=80),
    chassis: str = Query(..., min_length=1, max_length=40),
    limit: int = Query(default=4, ge=1, le=8),
):
    try:
        candidates = _commons_images(make, model, chassis, limit)
    except (HTTPError, URLError, OSError, ValueError, TimeoutError) as exc:
        raise HTTPException(
            503,
            "Wikimedia Commons is temporarily unavailable; bundled artwork remains accessible.",
        ) from exc
    return {
        "make": make,
        "model": model,
        "chassis": chassis,
        "photos": candidates,
        "source": "Wikimedia Commons",
        "review_required": True,
        "notice": (
            "Candidates have source attribution/license but require visual "
            "verification before using as the photo of an exact vehicle/engine."
        ),
    }
