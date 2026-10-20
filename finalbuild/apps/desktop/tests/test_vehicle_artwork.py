import hashlib
import json
from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication

from apps.desktop.vehicle_artwork import artwork_path, slug_piece, vehicle_pixmap


def test_catalog_portraits_are_transparent_and_packaged_for_each_native_client():
    root = Path(__file__).resolve().parents[3]
    entries = json.loads((root / "shared/vehicle_catalog.json").read_text())["vehicles"]
    for make, model, chassis in {(v["make"], v["model"], v["chassis"]) for v in entries}:
        portrait = artwork_path(make, model, chassis)
        assert portrait is not None, (make, model, chassis)
        with Image.open(portrait) as image:
            assert image.mode == "RGBA"
            alpha = image.getchannel("A")
            assert alpha.getextrema()[0] == 0
            assert alpha.getextrema()[1] > 200
            assert alpha.getbbox() is not None
        digest = hashlib.sha256(portrait.read_bytes()).digest()
        for folder in [
            "apps/mobile-android/app/src/main/assets/vehicle_models",
            "apps/mobile-ios/AICarScanner/VehicleModels",
        ]:
            copy = root / folder / portrait.name
            assert copy.is_file(), copy
            assert hashlib.sha256(copy.read_bytes()).digest() == digest


def test_unknown_model_cannot_resolve_to_a_different_vehicle():
    assert artwork_path("Unknown", "Unknown", "Unknown") is None
    assert artwork_path("Mercedes-Benz", "E-Class", "unknown") is None
    assert slug_piece("E140/E150") == "e140-e150"
    assert slug_piece("../unknown") == "unknown"


def test_native_portrait_and_fallback_render_with_requested_bounds():
    app = QApplication.instance() or QApplication([])
    for fields in [("Mercedes-Benz", "E-Class", "W211"), ("Unknown", "", "")]:
        pixmap = vehicle_pixmap(*fields, width=300, height=160)
        assert not pixmap.isNull()
        assert (pixmap.width(), pixmap.height()) == (300, 160)
        assert pixmap.hasAlphaChannel()
    app.processEvents()
