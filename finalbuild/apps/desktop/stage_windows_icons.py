"""Stage consistent Windows icon formats WITHOUT changing tracked source assets.

Uses a user-selected source PNG (or other Pillow-readable image) to build the
Desktop PNG, lossless WEBP, and multi-resolution ICO in an isolated build folder.
The staged files are passed to PyInstaller with AI_CAR_ICON_STAGE_DIR.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ICON_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def stage_icons(source: Path, output_dir: Path) -> tuple[Path, ...]:
    source = source.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Desktop icon source is missing: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    names = (
        "AI-Car-Scanner-master.png",
        "AI-Car-Scanner-mobile.png",
        "AI-Car-Scanner.webp",
        "AI-Car-Scanner.ico",
    )
    outputs = tuple(output_dir / name for name in names)
    if source in outputs:
        raise ValueError("Icon staging output must be separate from the source directory")

    with Image.open(source) as original:
        icon = original.convert("RGBA")
        if icon.width < 256 or icon.height < 256:
            icon = icon.resize((512, 512), Image.Resampling.LANCZOS)
        icon.save(outputs[0], format="PNG", optimize=True)
        icon.save(outputs[1], format="PNG", optimize=True)
        icon.save(outputs[2], format="WEBP", lossless=True, quality=100, method=6)
        icon.save(outputs[3], format="ICO", sizes=ICON_SIZES)

    for path in outputs:
        if not path.is_file() or path.stat().st_size < 128:
            raise RuntimeError(f"Staged icon missing/invalid: {path}")
    with Image.open(outputs[3]) as ico:
        if ico.format != "ICO" or (256, 256) not in ico.ico.sizes():
            raise ValueError("Staged ICO requires the 256x256 Windows icon frame")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_files = stage_icons(args.source, args.output_dir)
    print(f"[ICON] Source preserved: {args.source}")
    for path in output_files:
        print(f"[ICON] Staged: {path}")


if __name__ == "__main__":
    main()
