from pathlib import Path

import pytest
from PIL import Image

from apps.desktop import prepare_windows_icon as icons


def test_icon_builder_requires_android_launcher_asset(monkeypatch, tmp_path):
    missing = tmp_path / "missing.webp"
    monkeypatch.setattr(icons, "ANDROID_ICON", missing)
    with pytest.raises(FileNotFoundError, match="Android launcher icon not found"):
        icons.main()


def test_icon_builder_resizes_small_source_and_creates_all_desktop_formats(monkeypatch, tmp_path, capsys):
    source = tmp_path / "launcher.webp"
    Image.new("RGBA", (64, 64), (20, 100, 180, 255)).save(source, format="WEBP")
    webp = tmp_path / "assets" / "AI-Car-Scanner.webp"
    png = tmp_path / "assets" / "AI-Car-Scanner-mobile.png"
    ico = tmp_path / "assets" / "AI-Car-Scanner.ico"

    monkeypatch.setattr(icons, "ANDROID_ICON", source)
    monkeypatch.setattr(icons, "DESKTOP_WEBP", webp)
    monkeypatch.setattr(icons, "DESKTOP_PNG", png)
    monkeypatch.setattr(icons, "DESKTOP_ICO", ico)

    icons.main()

    assert all(path.is_file() and path.stat().st_size >= 128 for path in (webp, png, ico))
    with Image.open(webp) as image:
        assert image.format == "WEBP"
        assert image.size == (512, 512)
    with Image.open(png) as image:
        assert image.format == "PNG"
        assert image.mode == "RGBA"
    with Image.open(ico) as image:
        assert image.format == "ICO"
        assert image.width >= 16 and image.height >= 16
    assert "Generated Desktop PNG, WEBP, and Windows ICO" in capsys.readouterr().out
