from pathlib import Path
import runpy

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
    webp.parent.mkdir(parents=True, exist_ok=True)

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


def test_icon_builder_rejects_missing_generated_output(monkeypatch, tmp_path):
    source = tmp_path / "launcher.webp"
    Image.new("RGBA", (64, 64), (20, 100, 180, 255)).save(source, format="WEBP")
    webp = tmp_path / "assets" / "AI-Car-Scanner.webp"
    png = tmp_path / "assets" / "AI-Car-Scanner-mobile.png"
    ico = tmp_path / "assets" / "AI-Car-Scanner.ico"
    webp.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(icons, "ANDROID_ICON", source)
    monkeypatch.setattr(icons, "DESKTOP_WEBP", webp)
    monkeypatch.setattr(icons, "DESKTOP_PNG", png)
    monkeypatch.setattr(icons, "DESKTOP_ICO", ico)
    real_save = Image.Image.save

    def skip_webp_output(image, fp, *args, **kwargs):
        # Pillow can call Image.save() with an in-memory file object while
        # encoding formats; only intercept the explicit WEBP filesystem path.
        if isinstance(fp, (str, Path)) and Path(fp) == webp:
            return None
        return real_save(image, fp, *args, **kwargs)

    monkeypatch.setattr(Image.Image, "save", skip_webp_output)
    with pytest.raises(RuntimeError, match="Generated Desktop icon is missing or invalid"):
        icons.main()


def test_icon_builder_rejects_invalid_ico_header(monkeypatch, tmp_path):
    source = tmp_path / "launcher.webp"
    Image.new("RGBA", (64, 64), (20, 100, 180, 255)).save(source, format="WEBP")
    webp = tmp_path / "assets" / "AI-Car-Scanner.webp"
    png = tmp_path / "assets" / "AI-Car-Scanner-mobile.png"
    ico = tmp_path / "assets" / "AI-Car-Scanner.ico"
    webp.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(icons, "ANDROID_ICON", source)
    monkeypatch.setattr(icons, "DESKTOP_WEBP", webp)
    monkeypatch.setattr(icons, "DESKTOP_PNG", png)
    monkeypatch.setattr(icons, "DESKTOP_ICO", ico)
    real_open = Image.open

    class InvalidIconHeader:
        format = "PNG"
        width = 32
        height = 32

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def open_with_invalid_ico(path, *args, **kwargs):
        if Path(path) == ico:
            return InvalidIconHeader()
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(icons.Image, "open", open_with_invalid_ico)
    with pytest.raises(RuntimeError, match="Generated Windows icon failed validation"):
        icons.main()


def test_icon_script_entrypoint_runs_in_an_isolated_project_tree(
    monkeypatch, tmp_path, capsys
):
    project = tmp_path / "project"
    script_alias = project / "apps" / "desktop" / "prepare_windows_icon.py"
    launcher = (
        project / "apps" / "mobile-android" / "app" / "src" / "main"
        / "res" / "mipmap" / "ic_launcher.webp"
    )
    launcher.parent.mkdir(parents=True)
    (project / "assets").mkdir(parents=True)
    Image.new("RGBA", (64, 64), (20, 100, 180, 255)).save(launcher, format="WEBP")

    actual_script = Path(icons.__file__).resolve()
    real_resolve = Path.resolve

    def resolve_script_into_temporary_tree(path, *args, **kwargs):
        if path == actual_script:
            return script_alias
        return real_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_script_into_temporary_tree)
    runpy.run_path(str(actual_script), run_name="__main__")

    outputs = [
        project / "assets" / "AI-Car-Scanner.webp",
        project / "assets" / "AI-Car-Scanner-mobile.png",
        project / "assets" / "AI-Car-Scanner.ico",
    ]
    assert all(path.is_file() and path.stat().st_size >= 128 for path in outputs)
    assert "Generated Desktop PNG, WEBP, and Windows ICO" in capsys.readouterr().out
