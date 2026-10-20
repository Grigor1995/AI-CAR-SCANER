"""Offline make/model/chassis SVG illustration resolver for the Desktop UI."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def slug_piece(value: str) -> str:
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", (value or "").lower()))


def artwork_path(make: str, model: str, chassis: str) -> Path | None:
    root = (
        Path(getattr(sys, "_MEIPASS"))
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parents[2]
    )
    name = "_".join(map(slug_piece, (make, model, chassis))) + ".svg"
    destination = root / "assets" / "vehicle_models" / name
    return destination if destination.is_file() else None


def vehicle_pixmap(make: str, model: str, chassis: str, width: int = 420, height: int = 200) -> QPixmap:
    """Returns a model-matched illustration, with an offline branded fallback."""
    image = QPixmap(width, height)
    image.fill(Qt.GlobalColor.transparent)
    match = artwork_path(make, model, chassis)
    if match is not None:
        renderer = QSvgRenderer(str(match))
        if renderer.isValid():
            painter = QPainter(image)
            try:
                renderer.render(painter)
            finally:
                painter.end()
            return image
    root = (
        Path(getattr(sys, "_MEIPASS"))
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parents[2]
    )
    generic = QPixmap(str(root / "assets" / "AI-Car-Scanner-mobile.png"))
    if not generic.isNull():
        return generic.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return image
