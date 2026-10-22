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


def test_legacy_svg_assets_remain_valid_without_replacing_png_portraits():
    from PySide6.QtSvg import QSvgRenderer
    root = Path(__file__).resolve().parents[3]
    entries = json.loads((root / "shared/vehicle_catalog.json").read_text())["vehicles"]
    for make, model, chassis in {(v["make"], v["model"], v["chassis"]) for v in entries}:
        preferred = artwork_path(make, model, chassis)
        assert preferred.suffix == ".png"
        legacy = preferred.with_suffix(".svg")
        assert QSvgRenderer(str(legacy)).isValid(), str(legacy)


def test_svg_is_used_only_when_matching_png_is_missing(monkeypatch, tmp_path):
    from apps.desktop import vehicle_artwork
    directory = tmp_path / "assets/vehicle_models"
    directory.mkdir(parents=True)
    svg = directory / "test_car_x.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><rect width="100" height="50" fill="blue"/></svg>')
    monkeypatch.setattr(vehicle_artwork, "_root", lambda: tmp_path)
    assert artwork_path("Test", "Car", "X") == svg
    app = QApplication.instance() or QApplication([])
    image = vehicle_pixmap("Test", "Car", "X", 300, 160).toImage()
    assert not image.isNull()
    assert image.pixelColor(150, 80).alpha() > 0
    app.processEvents()


def test_backend_photo_is_async_cached_and_keeps_credit(monkeypatch):
    from io import BytesIO
    from types import SimpleNamespace
    from PySide6.QtWidgets import QLabel
    from PySide6 import QtNetwork
    from apps.desktop.vehicle_artwork import load_backend_portrait
    app = QApplication.instance() or QApplication([])
    content = BytesIO()
    Image.new('RGB', (24, 12), 'blue').save(content, format='PNG')
    replies = []
    class Reply:
        def __init__(self):
            self.callback = None
            self.finished = SimpleNamespace(connect=lambda callback: setattr(self, 'callback', callback))
            self.deleted = False
        def error(self): return QtNetwork.QNetworkReply.NoError
        def readAll(self): return content.getvalue()
        def rawHeader(self, name): return {b'X-Image-Credit':b'Photo%20Author',b'X-Image-License':b'CC BY 4.0',b'X-Image-Source':b'https://commons.wikimedia.org/wiki/File:Car.jpg'}[name]
        def deleteLater(self): self.deleted = True
    class Manager:
        def __init__(self, parent): pass
        def get(self, request):
            assert request.transferTimeout() == 5000
            assert 'make=Toyota' in request.url().toString()
            reply = Reply(); replies.append(reply); return reply
    monkeypatch.setattr(QtNetwork, 'QNetworkAccessManager', Manager)
    label = QLabel()
    load_backend_portrait(label, 'http://127.0.0.1:8001', 'Toyota', 'Corolla', 'E140/E150', 48, 24)
    assert label._backend_portrait is None  # The fetch has not completed.
    replies[0].callback()
    assert label._backend_portrait is not None and replies[0].deleted
    assert 'Photo Author' in label.toolTip() and 'CC BY 4.0' in label.toolTip()
    load_backend_portrait(label, 'http://127.0.0.1:8001', 'Toyota', 'Corolla', 'E140/E150', 48, 24)
    assert len(replies) == 1
    # A delayed previous selection must not replace the newly selected vehicle.
    load_backend_portrait(label, 'http://127.0.0.1:8001', 'Toyota', 'Camry', 'XV40', 48, 24)
    label.setProperty('backend_portrait_url', 'another selection')
    replies[1].callback()
    assert label._backend_portrait is None
    label.close(); label.deleteLater(); app.processEvents()
