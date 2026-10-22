"""Backend-only vehicle registry endpoints shared by Desktop/Android/iOS."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from vehicle.catalog_registry import makes, models, fitments, registry_stats
from vehicle.protocol.registry import all_protocols, assess_protocols, read_elm_detected_protocol
from vehicle.external_registry import (
    RemoteRegistryUnavailable, commons_photo_candidate, nhtsa_decode_vin
)

router = APIRouter(prefix="/api/v1/vehicle-registry", tags=["vehicle-registry"])


@router.get("/stats")
def stats():
    return registry_stats()


@router.get("/makes", response_model=list[str])
def global_makes(q: str = Query("", max_length=80)):
    return makes(q)


@router.get("/models")
def global_models(
    make: str = Query(..., min_length=1, max_length=80),
    year: int | None = Query(None, ge=1886, le=2100),
    q: str = Query("", max_length=80),
    limit: int = Query(200, ge=1, le=500),
):
    return models(make, year=year, query=q, limit=limit)


@router.get("/fitments")
def global_fitments(
    make: str = Query(..., min_length=1, max_length=80),
    model: str = Query(..., min_length=1, max_length=80),
    year: int | None = Query(None, ge=1886, le=2100),
):
    return fitments(make, model, year)


@router.get("/protocols")
def protocols():
    return {"protocols": all_protocols(), "real_vehicle_verification": "not_claimed"}


@router.get("/compatibility")
def compatibility(
    year: int = Query(..., ge=1886, le=2100),
    market: str = Query("unknown", max_length=24),
    make: str = Query("", max_length=80),
    fuel: str = Query("", max_length=64),
    vehicle_class: str = Query("passenger", max_length=40),
    detected_elm: str | None = Query(None, max_length=32),
):
    return assess_protocols(
        year=year, market=market, make=make,
        fuel=fuel, vehicle_class=vehicle_class,
        detected_elm=detected_elm,
    )


@router.get("/detected-elm")
def detected_elm(raw: str = Query(..., min_length=1, max_length=32)):
    return read_elm_detected_protocol(raw)


@router.get("/vin")
def vin_lookup(
    vin: str = Query(..., min_length=17, max_length=17),
    model_year: int | None = Query(None, ge=1980, le=2100),
):
    try:
        return nhtsa_decode_vin(vin, model_year)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RemoteRegistryUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/photo")
def photo(
    make: str = Query(..., min_length=1, max_length=80),
    model: str = Query(..., min_length=1, max_length=80),
    chassis: str = Query("", max_length=40),
):
    try:
        return commons_photo_candidate(make, model, chassis)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RemoteRegistryUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
