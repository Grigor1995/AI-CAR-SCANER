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
        if legacy.is_file():
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
        def rawHeader(self, name): return {'X-Image-Credit':b'Photo%20Author','X-Image-License':b'CC BY 4.0','X-Image-Source':b'https://commons.wikimedia.org/wiki/File:Car.jpg'}[name]
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


def test_real_qt_network_reply_loads_portrait_and_attribution(monkeypatch):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from io import BytesIO
    import sys
    from threading import Thread
    from time import monotonic
    from urllib.parse import quote
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QLabel
    from apps.desktop.vehicle_artwork import load_backend_portrait

    app = QApplication.instance() or QApplication([])
    content = BytesIO()
    Image.new('RGBA', (24, 12), (30, 100, 220, 255)).save(content, format='PNG')
    author = 'Լուսանկարիչ / Photo Author'
    errors = []
    monkeypatch.setattr(sys, 'excepthook', lambda *args: errors.append(args))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(content.getvalue())))
            self.send_header('X-Image-Credit', quote(author))
            self.send_header('X-Image-License', 'CC BY 4.0')
            self.send_header('X-Image-Source', 'https://commons.wikimedia.org/wiki/File:Car.jpg')
            self.end_headers()
            self.wfile.write(content.getvalue())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    label = QLabel()
    try:
        base_url = f'http://127.0.0.1:{server.server_port}'
        load_backend_portrait(label, base_url, 'Toyota', 'Corolla', 'E140/E150', 48, 24)
        deadline = monotonic() + 5
        while label._backend_portrait is None and not errors and monotonic() < deadline:
            app.processEvents()
            QTest.qWait(10)
        assert errors == [], errors
        assert label._backend_portrait is not None
        assert label.toolTip() == author+'\nCC BY 4.0\nhttps://commons.wikimedia.org/wiki/File:Car.jpg'
    finally:
        label.close()
        label.deleteLater()
        app.processEvents()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_catalog_neon_manifest_covers_all_generations_and_replaced_originals():
    root = Path(__file__).resolve().parents[3]
    manifest = json.loads((root / "assets/vehicle_models/neon-manifest.json").read_text())
    catalog = json.loads((root / "shared/vehicle_catalog.json").read_text())["vehicles"]
    expected = {(v["make"],v["model"],v["chassis"]) for v in catalog}
    actual = {(v["make"],v["model"],v["chassis"]) for v in manifest["vehicles"]}
    assert actual == expected
    assert manifest["style"] == "neon-blue-3d"
    for row in manifest["vehicles"]:
        assert row["sha256"] != row["original_sha256"]
        assert hashlib.sha256((root / "assets/vehicle_models" / row["name"]).read_bytes()).hexdigest() == row["sha256"]


def test_vehicle_neon_studio_preview_preserves_original_photo_pixels():
    """Neon blue rim must not overwrite or tint the exact vehicle portrait."""
    from PySide6.QtGui import QColor, QPixmap
    from apps.desktop.vehicle_artwork import NeonVehiclePreview
    app = QApplication.instance() or QApplication([])
    original = QPixmap(180, 90)
    original.fill(QColor(200, 33, 44))
    preview = NeonVehiclePreview()
    preview.setPixmap(original)
    assert preview.pixmap() is not None
    assert preview.pixmap().cacheKey() == original.cacheKey()
    assert "#26BFFF" in preview.styleSheet()
    preview.resize(320, 160)
    preview.show()
    app.processEvents()
    assert not preview.grab().isNull()
    preview.close()
    preview.deleteLater()

