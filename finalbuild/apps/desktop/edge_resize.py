"""Mouse resizing from a panel's right/bottom border; no extra controls."""
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QGroupBox


class EdgeResizablePanel(QGroupBox):
    size_saved = Signal(object)
    BORDER = 8

    def __init__(self, title=""):
        super().__init__(title)
        self.setMouseTracking(True)
        self._resize_origin = None
        self._resize_axes = (False, False)
        self._preferred_size = None

    def _edges(self, point):
        return (point.x() >= self.width()-self.BORDER,
                point.y() >= self.height()-self.BORDER)

    def ensure_readable_size(self):
        if self.layout():
            self.layout().activate()
        minimum = self.minimumSizeHint().expandedTo(QSize(280, 360))
        self._readable_minimum = minimum
        self.setMinimumSize(minimum)
        if self._preferred_size:
            size = self._preferred_size.expandedTo(minimum)
            self.setFixedSize(size)
        self.updateGeometry()

    def restore_size(self, size):
        try:
            width, height = (int(value) for value in size)
            if not (280 <= width <= 1600 and 360 <= height <= 1400):
                return
        except (TypeError, ValueError):
            return
        self._preferred_size = QSize(width, height)
        self.ensure_readable_size()

    def showEvent(self, event):
        self.ensure_readable_size()
        super().showEvent(event)

    def mousePressEvent(self, event):
        self.ensure_readable_size()
        axes = self._edges(event.position())
        if event.button() == Qt.LeftButton and any(axes):
            self._resize_origin = (event.globalPosition(), self.size())
            self._resize_axes = axes
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_origin is not None:
            start, size = self._resize_origin
            delta = event.globalPosition()-start
            horizontal, vertical = self._resize_axes
            width = size.width()+round(delta.x()) if horizontal else size.width()
            height = size.height()+round(delta.y()) if vertical else size.height()
            self._preferred_size = QSize(
                max(self._readable_minimum.width(), min(1600, width)),
                max(self._readable_minimum.height(), min(1400, height)))
            self.setFixedSize(self._preferred_size)
            self.updateGeometry()
            event.accept()
            return
        horizontal, vertical = self._edges(event.position())
        self.setCursor(Qt.SizeFDiagCursor if horizontal and vertical else
                       Qt.SizeHorCursor if horizontal else Qt.SizeVerCursor if vertical else Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resize_origin is not None and event.button() == Qt.LeftButton:
            self._resize_origin = None
            self.size_saved.emit([self.width(), self.height()])
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        if self._resize_origin is None:
            self.unsetCursor()
        super().leaveEvent(event)
