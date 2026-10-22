"""Backend-only regression for OBD standards and shared vehicle/photo APIs.

Does not contact hardware, Wikimedia or NHTSA. Unknown fitment cannot become
an asserted protocol merely because make/year resembles a known vehicle.
"""
from __future__ import annotations

import io
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.vehicle_catalog_routes import router
from vehicle_knowledge import catalog, images, protocols, vpic

client = TestClient(FastAPI())
client.app.include_router(router)


def test_all_generic_elm_modes_are_listed_but_enhanced_protocols_are_not_claimed_supported():
    found = {p["elm_id"]: p for p in protocols.OBD_PROTOCOLS if p["elm_id"]}
    assert set("123456789A") <= set(found)
    assert all(found[x]["supported_by_generic_elm"] for x in "123456789")
    assert not found["A"]["supported_by_generic_elm"]
    for standard in ("iso_14229_uds_can", "iso_14229_uds_doip", "iso_27145_wwh_obd"):
        assert protocols.get_protocol(standard)["supported_by_generic_elm"] is False


@pytest.mark.parametrize(
    ("raw", "expected", "auto"),
    [("A6", "iso_15765_4_11_500", True),
     ("ATDPN\r6\r>", "iso_15765_4_11_500", False),
     ("A3", "iso_9141_2", True),
     ("2", "sae_j1850_vpw", False),
     ("A0", None, True),
     ("garbage", None, False)],
)
def test_read_elm_report_without_inventing_unsupported_codes(raw, expected, auto):
    data = protocols.parse_elm_protocol(raw)
    assert (data["protocol"] or {}).get("id") == expected
    assert data["auto_selected"] is auto
    assert data["detected"] == bool(expected)


def test_older_vehicle_does_not_get_a_fake_ecu_protocol_confirmation():
    data = catalog.resolve_vehicle_protocols(
        make="Mercedes-Benz", model="E-Class", chassis="W211",
        engine="M272 E35 3.5", year=2006,
    )
    assert data["catalog_model_found"] is True
    assert data["curated_variants_found"] >= 1
    assert data["reported_protocol_id"] is None
    assert data["protocol_hints"]["confidence"] == "unverified_candidate"
    assert not data["protocol_hints"]["protocol_confirmed"]


def test_adapter_response_is_caller_supplied_not_cryptographically_attested():
    data = catalog.resolve_vehicle_protocols(
        make="Mercedes-Benz", model="E-Class", year=2006, adapter_report="A6"
    )
    assert data["reported_protocol_id"] == "iso_15765_4_11_500"
    assert data["observation_provenance"].startswith("caller_supplied_")


def test_broad_global_catalog_is_separate_from_exact_engine_variants():
    all_models = catalog.list_global_models(limit=500)
    curated = catalog.list_curated_variants(limit=500)
    assert all_models["total"] >= 200
    assert curated["total"] >= 50
    assert any(x["make"] == "Mercedes-Benz" for x in all_models["vehicles"])
    assert all(not x["fitment_verified"] for x in all_models["vehicles"])
    assert all(not x["vin_verified"] for x in curated["variants"])
    assert any("M272" in x["engine"] for x in curated["variants"])


def test_year_make_and_engine_filters_exclude_other_chassis():
    rows = catalog.list_curated_variants(
        make="Mercedes-Benz", model="E-Class", chassis="W211",
        engine="M272 E35 3.5", year=2006,
    )
    assert rows["total"] == 1
    assert rows["variants"][0]["chassis"] == "W211"
    assert catalog.list_curated_variants(
        make="Mercedes-Benz", model="E-Class", chassis="W211",
        engine="M272 E35 3.5", year=2025,
    )["total"] == 0


def test_public_backend_endpoints_return_one_shared_vehicle_catalog():
    protocols_response = client.get("/api/v1/vehicle-catalog/obd-protocols")
    assert protocols_response.status_code == 200
    assert len(protocols_response.json()["protocols"]) >= 16
    global_response = client.get("/api/v1/vehicle-catalog/global-models", params={"make": "BMW"})
    assert global_response.status_code == 200
    assert global_response.json()["total"] >= 3
    variants_response = client.get("/api/v1/vehicle-catalog/curated-variants", params={
        "make": "Mercedes-Benz", "chassis": "W211", "engine": "M272 E35 3.5",
    })
    assert variants_response.status_code == 200
    assert variants_response.json()["total"] == 1
    hints_response = client.get("/api/v1/vehicle-catalog/protocol-hints", params={
        "make": "Mercedes-Benz", "model": "E-Class", "year": 2006, "adapter_report": "A0",
    })
    assert hints_response.status_code == 200
    assert hints_response.json()["reported_protocol_id"] is None


def test_generated_project_portrait_is_never_mislabeled_real_photo():
    meta = images.bundled_image_metadata("Mercedes-Benz", "E-Class", "W211")
    assert meta["is_real_car_photo"] is False
    assert meta["image_kind"] == "generated_project_artwork"
    assert client.get("/api/v1/vehicle-catalog/artwork", params={
        "make": "Mercedes-Benz", "model": "E-Class", "chassis": "W211"
    }).status_code == 200


def test_licensed_commons_photo_candidates_include_author_and_visual_review(monkeypatch):
    def fake_open(request, timeout):
        assert "commons.wikimedia.org" in request.full_url
        response = {
            "query": {"pages": {
                "1": {
                    "title": "File:Mercedes-Benz W211 E-Class photo.jpg",
                    "imageinfo": [{
                        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/x/w211.jpg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Mercedes-Benz_W211_E-Class_photo.jpg",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY-SA 4.0"},
                            "UsageTerms": {"value": "Creative Commons Attribution-ShareAlike 4.0"},
                            "Artist": {"value": "<b>Example Photographer</b>"},
                        },
                    }],
                },
            }},
        }
        return io.BytesIO(json.dumps(response).encode())
    monkeypatch.setattr(images, "urlopen", fake_open)
    images.search_licensed_commons_photos.cache_clear()
    rows = images.search_licensed_commons_photos("Mercedes-Benz", "E-Class", "W211", 1)
    assert len(rows) == 1
    assert rows[0]["author"] == "Example Photographer"
    assert rows[0]["verification_status"].endswith("visual_model_review")
    images.search_licensed_commons_photos.cache_clear()


def test_noncommercial_photos_are_rejected_even_if_cc_by_prefix_matches():
    assert not images._license_accepted("CC BY-NC-SA 4.0", "NonCommercial")
    assert not images._license_accepted("CC BY-ND 4.0", "NoDerivatives")


def test_nhtsa_vpic_is_explicit_online_and_does_not_fabricate_engine_codes(monkeypatch):
    def fake_open(request, timeout):
        return io.BytesIO(json.dumps({"Results": [
            {"Model_Name": "Accord"}, {"Model_Name": "Civic"},
        ]}).encode())
    monkeypatch.setattr(vpic, "urlopen", fake_open)
    vpic.nhtsa_models_for_make_year.cache_clear()
    data = vpic.nhtsa_models_for_make_year("Honda", 2018)
    assert data["models"] == ["Accord", "Civic"]
    assert data["engine_details"] == "not_provided_by_this_endpoint"
    with pytest.raises(ValueError):
        vpic.nhtsa_models_for_make_year("../bad", 2018)
    vpic.nhtsa_models_for_make_year.cache_clear()


def test_backend_normalizes_adapter_protocol_for_all_native_clients():
    response = client.post("/api/v1/vehicle-catalog/parse-adapter-protocol", json={
        "adapter_id": "user-adapter",
        "atdpn": "A6",
        "atdp": "AUTO, ISO 15765-4 CAN (11/500)",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["protocol"]["id"] == "iso_15765_4_11_500"
    assert data["observation_provenance"] == "caller_supplied_not_backend_hardware_attested"
    malformed = client.post("/api/v1/vehicle-catalog/parse-adapter-protocol", json={
        "atdpn": "A" * 300
    })
    assert malformed.status_code == 422


def test_elm_text_description_must_not_be_mistaken_for_numeric_protocol_code():
    assert not protocols.parse_elm_protocol("ISO 15765-4 CAN (11/500)")["detected"]
    assert protocols.parse_elm_protocol("A")["protocol"]["id"] == "sae_j1939_250"
