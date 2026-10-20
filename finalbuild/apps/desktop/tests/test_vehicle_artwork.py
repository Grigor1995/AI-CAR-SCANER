"""Offline vehicle model images are available for every curated vehicle."""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from apps.desktop.vehicle_artwork import artwork_path, slug_piece, vehicle_pixmap


def test_artwork_slug_normalizes_chassis_and_model():
    assert slug_piece("E140/E150") == "e140-e150"
    assert slug_piece("3 Series") == "3-series"
    assert slug_piece(" Mercedes-Benz ") == "mercedes-benz"


def test_all_curated_model_chassis_combinations_have_valid_svg():
    root = Path(__file__).resolve().parents[3]
    entries = json.loads(
        (root / "shared" / "vehicle_catalog.json").read_text(encoding="utf-8")
    )["vehicles"]
    distinct = {(x["make"], x["model"], x["chassis"]) for x in entries}
    assert len(distinct) >= 22
    for make, model, chassis in distinct:
        image = artwork_path(make, model, chassis)
        assert image is not None and image.is_file(), (make, model, chassis)
        renderer = QSvgRenderer(str(image))
        assert renderer.isValid(), str(image)
        assert model in image.read_text(encoding="utf-8")


def test_model_image_and_fallback_render_without_network():
    app = QApplication.instance() or QApplication([])
    try:
        car = vehicle_pixmap("Mercedes-Benz", "E-Class", "W211", 300, 160)
        assert not car.isNull()
        assert car.width() == 300
        assert car.height() == 160

        fallback = vehicle_pixmap("Unknown", "Not-a-model", "XX", 300, 160)
        assert not fallback.isNull()
    finally:
        app.processEvents()
