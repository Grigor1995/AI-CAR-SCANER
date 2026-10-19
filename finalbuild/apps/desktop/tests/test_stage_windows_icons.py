"""Safe build artwork staging regression tests."""
from pathlib import Path
import hashlib

import pytest
from PIL import Image

from apps.desktop.stage_windows_icons import stage_icons


def test_stage_preserves_user_png_and_generates_consistent_assets(tmp_path):
    source = tmp_path / "user-design.png"
    Image.new("RGBA", (512, 512), (47, 120, 201, 233)).save(source)
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "build-output" / "icons"

    paths = stage_icons(source, output)

    assert len(paths) == 4
    assert all(file.is_file() for file in paths)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before_hash
    assert output != source.parent
    with Image.open(output / "AI-Car-Scanner-mobile.png") as png:
        assert png.size == (512, 512)
        assert png.mode == "RGBA"
        with Image.open(output / "AI-Car-Scanner.webp") as webp:
            assert png.convert("RGBA").tobytes() == webp.convert("RGBA").tobytes()
    with Image.open(output / "AI-Car-Scanner.ico") as ico:
        assert ico.format == "ICO"
        assert (256, 256) in ico.ico.sizes()


def test_stage_does_not_modify_source_when_upscaling(tmp_path):
    source = tmp_path / "edited.png"
    Image.new("RGBA", (64, 64), (15, 33, 80, 255)).save(source)
    initial = source.read_bytes()
    stage_icons(source, tmp_path / "release")
    assert source.read_bytes() == initial
    with Image.open(tmp_path / "release" / "AI-Car-Scanner-mobile.png") as image:
        assert image.size == (512, 512)


def test_stage_rejects_missing_source_and_source_inside_output(tmp_path):
    with pytest.raises(FileNotFoundError):
        stage_icons(tmp_path / "no.png", tmp_path / "stage")

    folder = tmp_path / "icons"
    folder.mkdir()
    source = folder / "AI-Car-Scanner-mobile.png"
    Image.new("RGBA", (256, 256), (10, 12, 15, 255)).save(source)
    with pytest.raises(ValueError, match="separate from the source"):
        stage_icons(source, folder)



def test_staging_accepts_tiny_but_valid_lossless_webp(tmp_path):
    """Simple artwork can encode to <128 bytes; decoding must decide validity."""
    source = tmp_path / "solid.png"
    Image.new("RGBA", (512, 512), (47, 120, 201, 233)).save(source)
    staged = tmp_path / "staged"
    stage_icons(source, staged)

    webp = staged / "AI-Car-Scanner.webp"
    assert webp.stat().st_size > 0
    with Image.open(webp) as image:
        assert image.format == "WEBP"
        assert image.size == (512, 512)
        image.verify()



def test_stage_cli_respects_explicit_paths_without_touching_source(monkeypatch, tmp_path, capsys):
    """Cover the build command used in Git Bash and its source preservation."""
    from apps.desktop import stage_windows_icons as staging

    source = tmp_path / "local-user-icon.png"
    Image.new("RGBA", (512, 512), (20, 40, 60, 230)).save(source, format="PNG")
    original = source.read_bytes()
    output = tmp_path / "isolated-build"
    monkeypatch.setattr(
        "sys.argv",
        ["stage_windows_icons.py", "--source", str(source), "--output-dir", str(output)],
    )

    staging.main()

    assert source.read_bytes() == original
    assert (output / "AI-Car-Scanner-mobile.png").is_file()
    assert (output / "AI-Car-Scanner.webp").is_file()
    assert (output / "AI-Car-Scanner.ico").is_file()
    output_text = capsys.readouterr().out
    assert "Source preserved" in output_text
    assert "Staged:" in output_text


def test_stage_invalid_png_does_not_overwrite_source(monkeypatch, tmp_path):
    source = tmp_path / "invalid-user-image.png"
    source.write_bytes(b"not a decodable image")
    before = source.read_bytes()
    with pytest.raises((OSError, ValueError)):
        stage_icons(source, tmp_path / "build-icons")
    assert source.read_bytes() == before
