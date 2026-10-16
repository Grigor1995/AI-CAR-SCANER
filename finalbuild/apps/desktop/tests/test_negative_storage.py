"""Negative persistent-vehicle data tests with isolated temp files.

These tests never touch the real user's APPDATA/vehicles.json.
"""
from __future__ import annotations

import pytest

from apps.desktop import storage
from apps.desktop.models import Vehicle


@pytest.fixture
def store(tmp_path, monkeypatch):
    folder = tmp_path / "AI-Car-Scanner"
    monkeypatch.setattr(storage, "APP_DIR", folder)
    monkeypatch.setattr(storage, "VEHICLES_FILE", folder / "vehicles.json")
    return storage.VehicleStore()


@pytest.mark.parametrize(
    "invalid_json",
    [
        "{not-json",
        "null",
        "42",
        '"string"',
        '{"vehicles": []}',
        '["bad-row"]',
        '[{"make":"Kia", "year":"not-a-year"}]',
    ],
)
def test_negative_corrupted_vehicle_storage_is_never_loaded(store, invalid_json):
    storage.VEHICLES_FILE.write_text(invalid_json, encoding="utf-8")
    assert store.load() == []


def test_negative_file_permission_error_on_load_falls_back_safely(store, monkeypatch):
    storage.VEHICLES_FILE.write_text("[]", encoding="utf-8")
    original = type(storage.VEHICLES_FILE).read_text

    def deny_read(path, *args, **kwargs):
        if path == storage.VEHICLES_FILE:
            raise PermissionError("access denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(type(storage.VEHICLES_FILE), "read_text", deny_read)
    assert store.load() == []


def test_negative_failed_save_reports_error_and_does_not_fabricate_success(store, monkeypatch):
    path_type = type(storage.VEHICLES_FILE)
    original = path_type.write_text

    def deny_write(path, *args, **kwargs):
        if path == storage.VEHICLES_FILE:
            raise PermissionError("disk read-only")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(path_type, "write_text", deny_write)
    with pytest.raises(PermissionError, match="disk read-only"):
        store.save([Vehicle("Kia", "Forte")])
    assert not storage.VEHICLES_FILE.exists()


def test_negative_empty_storage_data_does_not_create_fake_vehicle(store):
    storage.VEHICLES_FILE.write_text("[]", encoding="utf-8")
    assert store.load() == []
