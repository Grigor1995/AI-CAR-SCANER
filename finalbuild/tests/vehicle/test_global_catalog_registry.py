"""Shared vehicle models and engines come from the BACKEND registry only."""
from vehicle.catalog_registry import makes, models, fitments, registry_stats


def test_global_make_model_catalog_is_broader_than_mobile_seed():
    meta = registry_stats()
    assert meta["make_count"] >= 30
    assert meta["global_model_families"] > 100
    assert meta["curated_chassis_entries"] >= 22
    assert meta["worldwide_exhaustive"] is False
    assert meta["data_authority"] == "backend"


def test_makes_case_insensitive_lookup_is_sorted():
    assert "Mercedes-Benz" in makes("mercedes")
    assert all(x in makes() for x in ("BMW", "Toyota", "Kia"))


def test_models_require_existing_make_and_return_engine_family_scope():
    assert models("not-a-manufacturer") == []
    values = models("Mercedes-Benz", 2006)
    example = next(x for x in values if x["model"] == "E-Class")
    assert example["engine_scope"] == "family-level"
    assert example["engine_families"]
    assert "VIN" in example["disclaimer"]


def test_w211_chassis_engine_fitment_is_curated_not_vin_verified():
    row = fitments("Mercedes-Benz", "E-Class", 2006)
    w211 = next(x for x in row if x["chassis"] == "W211")
    assert "M272 E35 3.5" in [x["name"] for x in w211["engines"]]
    assert w211["scope"] == "selector_hint_not_vin_verified"


def test_fitments_are_filtered_by_year():
    assert not any(x["chassis"] == "W211" for x in fitments("Mercedes-Benz", "E-Class", 2026))
