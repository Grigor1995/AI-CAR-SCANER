"""Offline generated portraits, resolved by exact make/model/chassis."""
from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap, QImage
from PySide6.QtWidgets import QLabel


def slug_piece(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def artwork_path(make: str, model: str, chassis: str) -> Path | None:
    stem = "_".join(map(slug_piece, (make, model, chassis)))
    for extension in (".png", ".svg"):
        path = _root() / "assets" / "vehicle_models" / (stem + extension)
        if path.is_file():
            return path
    return None


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


def load_backend_portrait(label, base_url, make, model, chassis, width=420, height=200):
    """Display a local cache immediately; fetch backend artwork without blocking Qt."""
    from urllib.parse import urlencode, unquote
    from PySide6.QtCore import QUrl
    from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
    label.setPixmap(vehicle_pixmap(make, model, chassis, width, height))
    if not isinstance(base_url, str) or not base_url.startswith(("https://", "http://")) or not make or not model:
        return
    url = base_url.rstrip("/") + "/api/v1/vehicle-reference/image?" + urlencode({"make": make, "model": model, "chassis": chassis or ""})
    if label.property("backend_portrait_url") == url:
        cached = getattr(label, "_backend_portrait", None)
        if cached is not None:
            label.setPixmap(cached)
        return
    label.setProperty("backend_portrait_url", url)
    label._backend_portrait = None
    manager = getattr(label, "_portrait_manager", None)
    if manager is None:
        manager = QNetworkAccessManager(label)
        label._portrait_manager = manager
    request = QNetworkRequest(QUrl(url))
    request.setTransferTimeout(5000)
    reply = manager.get(request)
    def finished():
        try:
            if label.property("backend_portrait_url") == url and reply.error() == QNetworkReply.NoError:
                image = QImage.fromData(bytes(reply.readAll()))
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    label._backend_portrait = pixmap
                    label.setPixmap(pixmap)
                    credit = unquote(bytes(reply.rawHeader("X-Image-Credit")).decode())
                    license_name = bytes(reply.rawHeader("X-Image-License")).decode()
                    source = bytes(reply.rawHeader("X-Image-Source")).decode()
                    if credit or license_name:
                        label.setToolTip("\n".join([credit, license_name, source]))
        finally:
            reply.deleteLater()
    reply.finished.connect(finished)

class NeonVehiclePreview(QLabel):
    """Studio-glass presentation for exact make/model artwork, preserving photo pixels.

    The source bitmap (including backend credit metadata) is not recolored. The
    cyan gradient and rim are native Qt stylesheet decoration behind the pixmap.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(9, 7, 9, 7)
        self.setStyleSheet(
            "QLabel {"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #03070E, stop:0.52 #0A2941, stop:1 #041321);"
            "border: 2px solid #26BFFF; border-radius: 17px;"
            "padding: 5px; }"
        )
