"""Optional online US NHTSA vPIC make/model/year lookup.

vPIC is a US regulatory dataset; it does not guarantee all makes worldwide or
a VIN-level engine fitment. No automatic VIN transmission to a third party.
"""
from __future__ import annotations

from functools import lru_cache
import json
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
