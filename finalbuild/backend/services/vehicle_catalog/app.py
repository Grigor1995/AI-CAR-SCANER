"""Run independently: python -m uvicorn services.vehicle_catalog.app:app --port 8011.

The process owns only the immutable catalog/fitment data and pure protocol hints.
It intentionally does not import API state, database engines or account models.
"""
import secrets
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from .port import credential, embedded
from .correlation import install

app = FastAPI(title="AI Car Vehicle Catalog", version="1.0.0")
install(app)

def authorize(authorization: str = Header("")):
    expected = "Bearer " + credential()
    if not secrets.compare_digest(authorization.encode(), expected.encode()):
        raise HTTPException(401, "Service authentication required")

@app.get("/health")
def health(): return {"service": "vehicle-catalog", "status": "alive", "api_version": "v1"}

@app.get("/ready", dependencies=[Depends(authorize)])
def ready():
    embedded("stats", {})
    return {"status": "ready"}

@app.get("/internal/v1/catalog/stats", dependencies=[Depends(authorize)])
def stats(): return embedded("stats", {})

@app.get("/internal/v1/catalog/makes", dependencies=[Depends(authorize)])
def makes(query: str = Query("", max_length=80)):
    return embedded("makes", {"query": query})

@app.get("/internal/v1/catalog/models", dependencies=[Depends(authorize)])
def models(make: str = Query(..., min_length=1, max_length=80), year: int | None = Query(None, ge=1886, le=2100),
           query: str = Query("", max_length=80), limit: int = Query(200, ge=1, le=500)):
    return embedded("models", dict(make=make, year=year, query=query, limit=limit))

@app.get("/internal/v1/catalog/fitments", dependencies=[Depends(authorize)])
def fitments(make: str = Query(..., min_length=1, max_length=80), model: str = Query(..., min_length=1, max_length=80),
             year: int | None = Query(None, ge=1886, le=2100)):
    return embedded("fitments", dict(make=make, model=model, year=year))

@app.get("/internal/v1/catalog/profile", dependencies=[Depends(authorize)])
def profile(make: str = Query(..., min_length=1, max_length=80), model: str = Query(..., min_length=1, max_length=80),
            year: int = Query(..., ge=1886, le=2100), market: str = Query("unknown", max_length=24),
            engine: str = Query("", max_length=100), chassis: str = Query("", max_length=40),
            fuel: str = Query("", max_length=64), vehicle_class: str = Query("passenger", max_length=40),
            detected_elm: str | None = Query(None, max_length=32)):
    return embedded("profile", dict(make=make, model=model, year=year, market=market, engine=engine,
                                   chassis=chassis, fuel=fuel, vehicle_class=vehicle_class, detected_elm=detected_elm))
