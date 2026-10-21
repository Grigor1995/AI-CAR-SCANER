"""Offline generated portraits, resolved by exact make/model/chassis."""
from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap, QImage


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


@lru_cache(maxsize=96)
def _portrait_image(path: str, modified: int, width: int, height: int) -> QImage:
    # Cache CPU-side images, not QPixmaps whose lifetime depends on QApplication.
    canvas = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    portrait = QImage(path)
    if not portrait.isNull():
        portrait = portrait.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
        painter = QPainter(canvas)
        try:
            painter.drawImage((width - portrait.width()) // 2,
                              (height - portrait.height()) // 2, portrait)
        finally:
            painter.end()
    return canvas


def vehicle_pixmap(make: str, model: str, chassis: str, width: int = 420, height: int = 200) -> QPixmap:
    path = artwork_path(make, model, chassis) or (_root() / "assets" / "AI-Car-Scanner-mobile.png")
    modified = path.stat().st_mtime_ns if path.is_file() else 0
    return QPixmap.fromImage(_portrait_image(str(path), modified, width, height))
