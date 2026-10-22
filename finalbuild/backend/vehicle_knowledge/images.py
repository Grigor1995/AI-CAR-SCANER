"""Shared backend image metadata and safe Wikimedia Commons photo discovery.

Portraits already bundled with the repo are generated art, never presented as
photographs. Real-image search is explicitly opt-in and returns fully attributed
Wikimedia Commons candidate metadata, not silently selected "verified" photos.
"""
from __future__ import annotations

from functools import lru_cache
from html import unescape
import json
from pathlib import Path
import sys
import re
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = (
    Path(sys._MEIPASS) if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parents[2]
)
ARTWORK = ROOT / "assets" / "vehicle_models"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
LICENSE_TOKENS = ("CC BY", "CC-BY", "CC0", "PUBLIC DOMAIN", "PD-")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def bundled_model_artwork(make: str, model: str, chassis: str) -> Path | None:
    """No traversal; known root only, use canonical make/model/chassis-derived name."""
    basename = "_".join(_slug(x) for x in (make, model, chassis))
    for extension in (".png", ".svg"):
        candidate = ARTWORK / f"{basename}{extension}"
        if candidate.is_file():
            return candidate
    return None


def bundled_image_metadata(make: str, model: str, chassis: str) -> dict[str, Any]:
    file = bundled_model_artwork(make, model, chassis)
    return {
        "image_kind": "generated_project_artwork" if file else "unavailable",
        "uri": (
            "/api/v1/vehicle-catalog/artwork?"
            + urlencode({"make": make, "model": model, "chassis": chassis})
            if file else None
        ),
        "file_format": file.suffix[1:] if file else None,
        "is_real_car_photo": False,
        "attribution": "AI-CAR-SCANER project-generated vehicle portrait" if file else None,
        "photo_search_endpoint": "/api/v1/vehicle-catalog/commons-photo-candidates",
    }


def _plaintext(value: Any) -> str:
    return unescape(re.sub(r"<[^>]*>", "", str(value or ""))).strip()


def _license_accepted(license_name: str, usage: str) -> bool:
    value = license_name.upper().replace("_", " ")
    terms = usage.upper().replace("_", " ")
    restricted = (
        "NONCOMMERCIAL", "NON-COMMERCIAL", "NO DERIV", "FAIR USE",
        "CC BY-NC", "CC-BY-NC", "CC BY-ND", "CC-BY-ND",
        " CC NC", " CC ND",
    )
    return (
        any(t in value for t in LICENSE_TOKENS)
        and not any(t in value or t in terms for t in restricted)
    )


@lru_cache(maxsize=128)
def search_licensed_commons_photos(make: str, model: str, chassis: str, limit: int = 4) -> list[dict[str, Any]]:
    if not 1 <= limit <= 8:
        raise ValueError("limit must be 1..8")
    if not make.strip() or not model.strip() or not chassis.strip():
        return []
    # Search File namespace, not Wikipedia article pageimages. Limit time,
    # source host, and response size. All returns require human visual review.
    query = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f'filetype:bitmap {make} {model} {chassis}',
        "gsrnamespace": "6",
        "gsrlimit": str(min(limit * 4, 28)),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": "960",
    }
    request = Request(
        WIKIMEDIA_API + "?" + urlencode(query),
        headers={"User-Agent": "AI-CAR-SCANER/0.6 (Wikimedia Commons attribution and vehicle-image research)"},
    )
    with urlopen(request, timeout=7) as response:
        # Bound memory even if upstream starts sending a huge or invalid reply.
        data = json.loads(response.read(2_000_000).decode("utf-8"))
    pages = (data.get("query") or {}).get("pages") or {}
    matches: list[dict[str, Any]] = []
    for page in pages.values():
        if not isinstance(page, dict) or not page.get("title", "").lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            continue
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        license_name = _plaintext((meta.get("LicenseShortName") or {}).get("value"))
        usage = _plaintext((meta.get("UsageTerms") or {}).get("value"))
        if not _license_accepted(license_name, usage):
            continue
        title = str(page["title"])
        if chassis.casefold() not in title.casefold():
            # Avoid showing a different generation as a verified model photo.
            continue
        thumb = info.get("thumburl") or info.get("url")
        file_page = info.get("descriptionurl")
        if not thumb or not str(thumb).startswith("https://upload.wikimedia.org/"):
            continue
        if not file_page or not str(file_page).startswith("https://commons.wikimedia.org/wiki/"):
            continue
        matches.append({
            "title": title,
            "image_url": thumb,
            "file_page": file_page,
            "author": _plaintext((meta.get("Artist") or {}).get("value"))[:500],
            "license": license_name,
            "license_url": (meta.get("LicenseUrl") or {}).get("value"),
            "attribution_required": True,
            "verification_status": "licensed_candidate_requires_visual_model_review",
            "image_kind": "real_vehicle_photograph_candidate",
            "source": "Wikimedia Commons API",
        })
        if len(matches) == limit:
            break
    return matches
