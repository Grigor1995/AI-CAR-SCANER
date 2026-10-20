"""Offline generated portraits, resolved by exact make/model/chassis."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap


def slug_piece(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def artwork_path(make: str, model: str, chassis: str) -> Path | None:
    filename = "_".join(map(slug_piece, (make, model, chassis))) + ".png"
    path = _root() / "assets" / "vehicle_models" / filename
    return path if path.is_file() else None


def vehicle_pixmap(make: str, model: str, chassis: str, width: int = 420, height: int = 200) -> QPixmap:
    """Contain the whole car without stretching; unmatched models use app branding."""
    canvas = QPixmap(width, height)
    canvas.fill(Qt.GlobalColor.transparent)
    match = artwork_path(make, model, chassis)
    portrait = QPixmap(str(match or (_root() / "assets" / "AI-Car-Scanner-mobile.png")))
    if not portrait.isNull():
        portrait = portrait.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
        painter = QPainter(canvas)
        try:
            painter.drawPixmap((width - portrait.width()) // 2,
                               (height - portrait.height()) // 2, portrait)
        finally:
            painter.end()
    return canvas
