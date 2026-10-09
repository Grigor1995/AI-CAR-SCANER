from __future__ import annotations
import json
import os
from pathlib import Path
from .models import Vehicle

APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "AI-Car-Scanner"
VEHICLES_FILE = APP_DIR / "vehicles.json"

class VehicleStore:
    def __init__(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[Vehicle]:
        if not VEHICLES_FILE.exists():
            return []
        try:
            data = json.loads(VEHICLES_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                return []
            return [Vehicle.from_json(item) for item in data]
        except (OSError, ValueError, TypeError, AttributeError):
            return []

    def save(self, vehicles: list[Vehicle]) -> None:
        VEHICLES_FILE.write_text(json.dumps([v.to_json() for v in vehicles], ensure_ascii=False, indent=2), encoding="utf-8")
