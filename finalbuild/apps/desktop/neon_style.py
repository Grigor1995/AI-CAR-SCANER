"""Shared Desktop neon-blue presentation primitives.

Painted at runtime with native Qt: vehicle photos remain the original
make/model/chassis artwork, framed by UI effects rather than recolored or replaced.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import (
    QColor, QPainter, QPen, QLinearGradient, QRadialGradient,
    QPainterPath, QPixmap,
)
from PySide6.QtWidgets import QWidget, QLabel


NEON_CYAN = QColor("#00AEEF")
NEON_LIGHT = QColor("#79E3FF")
NEON_NAVY = QColor("#030304")


def _asset_root() -> Path:
    return Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]


class NeonShell(QWidget):
    """Subtle photo-backed dark background without network requests or animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("desktopShell")
        self.dark_theme = True
        self._image = QPixmap(str(_asset_root() / "assets" / "launcher" / "background.png"))
        self._cached_size = QSize()
        self._scaled = QPixmap()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        rect = self.rect()
        if not self.dark_theme:
            painter.fillRect(rect, QColor("#F0F6FC"))
            painter.end()
            return
        painter.fillRect(rect, NEON_NAVY)
        if not self._image.isNull():
            if rect.size() != self._cached_size:
                self._cached_size = rect.size()
                self._scaled = self._image.scaled(
                    rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
            painter.setOpacity(0.38)
            painter.drawPixmap(
                (rect.width() - self._scaled.width()) // 2,
                (rect.height() - self._scaled.height()) // 2,
                self._scaled,
            )
            painter.setOpacity(1.0)
        overlay = QLinearGradient(0, 0, rect.width(), rect.height())
        overlay.setColorAt(0, QColor(3, 3, 4, 182))
        overlay.setColorAt(0.52, QColor(5, 15, 27, 147))
        overlay.setColorAt(1, QColor(0, 18, 32, 181))
        painter.fillRect(rect, overlay)
        painter.setPen(QPen(QColor(0, 174, 239, 28), 1))
        for x in range(0, rect.width(), 92):
            painter.drawLine(x, 0, x, rect.height())
        for y in range(0, rect.height(), 92):
            painter.drawLine(0, y, rect.width(), y)
        painter.end()


class NeonVehiclePreview(QLabel):
    """Draw an actual vehicle photo above a neon-blue automotive studio backdrop."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("neonVehiclePreview")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(140)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        outer = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        if outer.width() <= 0 or outer.height() <= 0:
            return
        path = QPainterPath()
        path.addRoundedRect(outer, 17, 17)
        painter.setClipPath(path)
        background = QLinearGradient(outer.topLeft(), outer.bottomRight())
        background.setColorAt(0, QColor("#030304"))
        background.setColorAt(0.5, QColor("#0B2A43"))
        background.setColorAt(1, QColor("#04101B"))
        painter.fillPath(path, background)
        highlight = QRadialGradient(outer.center().x(), outer.bottom() + 40, max(90.0, outer.width() * 0.7))
        highlight.setColorAt(0, QColor(0, 174, 239, 85))
        highlight.setColorAt(1, QColor(0, 174, 239, 0))
        painter.fillRect(outer, highlight)
        painter.setPen(QPen(QColor(25, 147, 200, 24), 1))
        for index in range(1, 7):
            y = outer.top() + index * outer.height() / 7
            painter.drawLine(outer.left() + 12, y, outer.right() - 12, y)

        car = self.pixmap()
        if car is not None and not car.isNull():
            fit = car.size()
            fit.scale(max(1, int(outer.width() - 26)), max(1, int(outer.height() - 22)), Qt.KeepAspectRatio)
            x = outer.center().x() - fit.width() / 2
            y = outer.center().y() - fit.height() / 2
            painter.drawPixmap(QRectF(x, y, fit.width(), fit.height()),
                               car, QRectF(car.rect()))
        painter.setClipping(False)
        # Layered rims make a shallow 3D/glass impression without blurring the car.
        painter.setBrush(Qt.NoBrush)
        for thickness, alpha in ((6, 23), (3, 48), (1, 175)):
            painter.setPen(QPen(QColor(0, 174, 239, alpha), thickness))
            painter.drawRoundedRect(outer.adjusted(thickness, thickness, -thickness, -thickness), 16, 16)
        painter.setPen(QPen(NEON_LIGHT, 2))
        painter.drawLine(int(outer.left() + 24), int(outer.top() + 2),
                         int(outer.center().x()), int(outer.top() + 2))
        painter.end()
