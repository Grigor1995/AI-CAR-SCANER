import json

from apps.desktop import storage
from apps.desktop.models import Vehicle


def test_load_returns_empty_when_file_does_not_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(storage, "VEHICLES_FILE", tmp_path / "app" / "vehicles.json")

    assert storage.VehicleStore().load() == []


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(storage, "VEHICLES_FILE", tmp_path / "app" / "vehicles.json")
    store = storage.VehicleStore()
    vehicles = [Vehicle("Mercedes-Benz", "E-Class", "W211", 2006, "M272", ["petrol", "lpg"], "ME9.7")]

    store.save(vehicles)

    assert store.load() == vehicles
    assert json.loads(storage.VEHICLES_FILE.read_text(encoding="utf-8"))[0]["year"] == 2006


def test_load_handles_corrupt_json_and_invalid_shape(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "APP_DIR", tmp_path / "app")
    file_path = tmp_path / "app" / "vehicles.json"
    monkeypatch.setattr(storage, "VEHICLES_FILE", file_path)
    storage.VehicleStore()
    file_path.write_text("{broken", encoding="utf-8")
    assert storage.VehicleStore().load() == []

    file_path.write_text('{"not": "a list"}', encoding="utf-8")
    assert storage.VehicleStore().load() == []


def test_load_handles_missing_fields_in_vehicle_records(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "APP_DIR", tmp_path / "app")
    file_path = tmp_path / "app" / "vehicles.json"
    monkeypatch.setattr(storage, "VEHICLES_FILE", file_path)
    storage.VehicleStore()
    file_path.write_text('[{"make":"Kia","model":"Forte"}]', encoding="utf-8")

    loaded = storage.VehicleStore().load()

    assert len(loaded) == 1
    assert loaded[0].make == "Kia"
    assert loaded[0].year is None
