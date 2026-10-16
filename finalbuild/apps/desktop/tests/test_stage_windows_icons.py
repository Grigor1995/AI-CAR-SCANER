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
