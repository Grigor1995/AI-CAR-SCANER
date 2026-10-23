"""Regression coverage for the experimental native neon Desktop design."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QSlider

from apps.desktop.neon_style import NeonShell, NeonVehiclePreview
from apps.desktop.neon_icon_build import render_neon_icon
from apps.desktop.ui import LiveDataPage, NEON_DESKTOP_QSS, APP_QSS_LIGHT


@pytest.fixture(scope="module")
def qt_app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_neon_icon_renders_from_brand_neutral_master(qt_app, tmp_path):
    root = Path(__file__).resolve().parents[3]
    source = root / "assets/design-preview/ai-scanner-neon-car-icon.svg"
    destination = tmp_path / "neon-icon.png"
    assert render_neon_icon(source, destination, 512) == destination
    image = QImage(str(destination))
    assert not image.isNull()
    assert image.size().width() == 512
    assert image.size().height() == 512
    assert image.pixelColor(512 // 2, 512 // 2).alpha() > 0


def test_neon_car_preview_paints_actual_pixmap(qt_app):
    widget = NeonVehiclePreview()
    widget.resize(420, 205)
    photo = QPixmap(240, 100)
    photo.fill(Qt.white)
    widget.setPixmap(photo)
    output = QImage(420, 205, QImage.Format_ARGB32)
    output.fill(Qt.transparent)
    widget.render(output)
    assert output.pixelColor(210, 100).alpha() == 255
    assert output.pixelColor(210, 100).red() >= 200
    widget.close()
    widget.deleteLater()


def test_dark_neon_theme_has_slider_and_light_mode_keeps_separate_palette():
    assert "QSlider::handle:horizontal" in NEON_DESKTOP_QSS
    assert "#00AEEF" in NEON_DESKTOP_QSS
    assert "#F0F6FC" in APP_QSS_LIGHT


def test_desktop_simulator_has_accessible_slider_controls(qt_app):
    class FakeAPI:
        pass

    class FakeSettings:
        def value(self, *_args):
            return "metric"

    class FakeApp:
        settings_store = FakeSettings()
        api = FakeAPI()

        def start_bound_acquisition(self): pass
        def start_simulator(self): pass
        def stop_simulator(self): pass
        def analyze_telemetry(self): pass
        def ai_analyze_live_data(self): pass
        def _apply_simulator_values(self): pass

    page = LiveDataPage(FakeApp())
    assert set(page.sim_sliders) == {"rpm", "coolant_c", "speed_kmh", "throttle_percent"}
    assert all(isinstance(sl, QSlider) for sl in page.sim_sliders.values())
    for key, slider in page.sim_sliders.items():
        assert isinstance(page.sim_inputs[key], QDoubleSpinBox)
        slider.setValue(slider.minimum() + 1)
        assert page.sim_inputs[key].value() == slider.value()
    page.close()
    page.deleteLater()
