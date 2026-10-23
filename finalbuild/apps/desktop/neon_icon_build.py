"""Render the brand-neutral neon app icon to a staged PNG, preserving tracked art.

QtSvg ships with PySide6 and supports the gradients and rounded paths used
by the approved vector master. Use the normal icon-staging tool afterward
to create Windows multi-resolution ICO and lossless WEBP.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def render_neon_icon(source: Path, destination: Path, size: int = 512) -> Path:
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("Icon output must be different from source")
    if not source.is_file():
        raise FileNotFoundError(f"Missing neon icon master: {source}")
    if not 256 <= size <= 2048:
        raise ValueError("Icon size must be between 256 and 2048")
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise ValueError(f"Invalid neon SVG: {source}")
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
    finally:
        painter.end()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(destination), "PNG"):
        raise RuntimeError(f"Could not save rendered icon: {destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=512)
    args = parser.parse_args()
    # QSvgRenderer can rasterize after the Qt GUI runtime has been initialized.
    app = QGuiApplication.instance() or QGuiApplication([])
    result = render_neon_icon(args.svg, args.output, args.size)
    print(f"[NEON ICON] Rendered brand-neutral icon: {result}")
    del app


if __name__ == "__main__":
    main()
