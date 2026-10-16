"""Desktop icon verification failure matrix using isolated files and Qt mocks.

Do not modify real desktop assets, require real hardware, or start an API.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PIL import Image

from apps.desktop import verify_icons
from apps.desktop.stage_windows_icons import stage_icons


@pytest.fixture
def icon_assets(monkeypatch, tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (512, 512), (44, 120, 190, 230)).save(source, format="PNG")
    assets = tmp_path / "staged-icons"
    stage_icons(source, assets)
    report = tmp_path / "report.json"
    monkeypatch.setenv("AI_CAR_VERIFY_ASSET_DIR", str(assets))
    monkeypatch.setenv("AI_CAR_ICON_REPORT_PATH", str(report))
    monkeypatch.setattr(verify_icons, "_embedded_icon_count", lambda: None)
    monkeypatch.setattr(
        verify_icons,
        "QGuiApplication",
        SimpleNamespace(instance=lambda: object()),
    )
    valid_icon = Mock()
    valid_icon.isNull.return_value = False
    valid_icon.pixmap.return_value.isNull.return_value = False
    monkeypatch.setattr(verify_icons, "QIcon", lambda _path: valid_icon)
    return assets, report, valid_icon


def test_verify_staged_icon_pack_succeeds_without_real_windows_executable(icon_assets):
    assets, report, icon = icon_assets
    assert verify_icons.verify_icons() == 0
    document = json.loads(report.read_text(encoding="utf-8"))
    assert document["status"] == "PASS"
    assert document["checks"]["png_webp_parity"] is True
    assert "ico_sizes" in document["checks"]
    assert document["checks"]["qt_window_icon"] is True
    icon.pixmap.assert_called_once_with(64, 64)


@pytest.mark.parametrize(
    "missing_name",
    ("AI-Car-Scanner-mobile.png", "AI-Car-Scanner.webp", "AI-Car-Scanner.ico"),
)
def test_negative_missing_staged_icon_fails_with_named_error(icon_assets, missing_name):
    assets, report, _ = icon_assets
    (assets / missing_name).unlink()
    assert verify_icons.verify_icons() == 1
    errors = json.loads(report.read_text(encoding="utf-8"))["errors"]
    assert any(missing_name in item for item in errors)


def test_negative_bad_image_bytes_are_rejected(icon_assets):
    assets, report, _ = icon_assets
    (assets / "AI-Car-Scanner.webp").write_bytes(b"corrupted image")
    assert verify_icons.verify_icons() == 1
    assert json.loads(report.read_text(encoding="utf-8"))["status"] == "FAIL"


def test_negative_small_png_is_rejected(icon_assets):
    assets, report, _ = icon_assets
    Image.new("RGBA", (32, 32), (255, 0, 0, 255)).save(assets / "AI-Car-Scanner-mobile.png")
    assert verify_icons.verify_icons() == 1
    assert any("smaller than 256" in error for error in json.loads(report.read_text(encoding="utf-8"))["errors"])


def test_negative_webp_size_mismatch_is_rejected(icon_assets):
    assets, report, _ = icon_assets
    Image.new("RGBA", (300, 300), (44, 120, 190, 230)).save(
        assets / "AI-Car-Scanner.webp", format="WEBP", lossless=True
    )
    assert verify_icons.verify_icons() == 1
    assert any("dimensions differ" in error for error in json.loads(report.read_text(encoding="utf-8"))["errors"])


def test_negative_webp_alpha_mismatch_is_rejected(icon_assets):
    assets, report, _ = icon_assets
    Image.new("RGBA", (512, 512), (44, 120, 190, 0)).save(
        assets / "AI-Car-Scanner.webp", format="WEBP", lossless=True
    )
    assert verify_icons.verify_icons() == 1
    assert any("alpha channels differ" in error for error in json.loads(report.read_text(encoding="utf-8"))["errors"])


def test_negative_webp_visible_colors_mismatch_is_rejected(icon_assets):
    assets, report, _ = icon_assets
    Image.new("RGBA", (512, 512), (230, 2, 10, 230)).save(
        assets / "AI-Car-Scanner.webp", format="WEBP", lossless=True
    )
    assert verify_icons.verify_icons() == 1
    assert any("differ visually" in error for error in json.loads(report.read_text(encoding="utf-8"))["errors"])


def test_negative_icon_without_256_frame_is_rejected(icon_assets):
    assets, report, _ = icon_assets
    Image.new("RGBA", (32, 32), (10, 90, 10, 255)).save(
        assets / "AI-Car-Scanner.ico", format="ICO"
    )
    assert verify_icons.verify_icons() == 1
    assert any("256x256 frame" in error for error in json.loads(report.read_text(encoding="utf-8"))["errors"])


@pytest.mark.parametrize("native_icon_count", [None, 0, 3])
def test_windows_native_exe_icon_count_is_validated_when_available(
    icon_assets, monkeypatch, native_icon_count
):
    _assets, report, _ = icon_assets
    monkeypatch.setattr(verify_icons, "_embedded_icon_count", lambda: native_icon_count)
    expected = 1 if native_icon_count == 0 else 0
    assert verify_icons.verify_icons() == expected
    data = json.loads(report.read_text(encoding="utf-8"))
    if native_icon_count:
        assert data["checks"]["embedded_exe_icon_count"] == native_icon_count


def test_negative_qt_fails_to_decode_icon(icon_assets, monkeypatch):
    _assets, report, fake_icon = icon_assets
    fake_icon.pixmap.return_value.isNull.return_value = True
    assert verify_icons.verify_icons() == 1
    assert any("Qt could not decode" in error for error in json.loads(report.read_text(encoding="utf-8"))["errors"])


def test_negative_invalid_json_report_target_fails_safely(icon_assets, monkeypatch, tmp_path):
    _assets, _report, _ = icon_assets
    blocked = tmp_path / "existing-file"
    blocked.write_text("occupied", encoding="utf-8")
    monkeypatch.setenv("AI_CAR_ICON_REPORT_PATH", str(blocked / "report.json"))
    assert verify_icons.verify_icons() == 1
