"""Local, persistent layout controls for native dashboard widgets."""
from __future__ import annotations

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSlider, QPushButton, QScrollArea


class MoveHandle(QPushButton):
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.parent().key)
            drag.setMimeData(mime)
            drag.exec(Qt.MoveAction)
        else:
            super().mouseMoveEvent(event)


class WidgetTile(QWidget):
    def __init__(self, board, key, content, width, height):
        super().__init__(board)
        self.board, self.key = board, key
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; border-radius: 3px; background: #294563; }
            QSlider::sub-page:horizontal { background: #168EED; border-radius: 3px; }
            QSlider::handle:horizontal { background: #68C5FF; width: 15px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #B0E3FF; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        toolbar = QHBoxLayout()
        self.handle = MoveHandle("⠿", self)
        self.handle.setToolTip("Drag to move widget")
        toolbar.addWidget(self.handle)
        for text, offset in (("←", -1), ("→", 1)):
            button = QPushButton(text)
            button.setToolTip("Move widget")
            button.clicked.connect(lambda _checked=False, step=offset: board.move(key, step))
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        sizes = QHBoxLayout()
        self.width_slider = QSlider(Qt.Horizontal)
        self.height_slider = QSlider(Qt.Horizontal)
        for slider, title, low, high, default in (
            (self.width_slider, "Widget width", 260, 1100, width),
            (self.height_slider, "Widget height", 150, 1200, height),
        ):
            slider.setAccessibleName(title)
            slider.setToolTip(title)
            slider.setRange(low, high)
            try:
                saved = int(board.settings.value(f"{board.prefix}/{key}/{title}", default)) if board.settings else default
            except (TypeError, ValueError):
                saved = default
            slider.setValue(saved)
            sizes.addWidget(QLabel("↔" if slider is self.width_slider else "↕"))
            sizes.addWidget(slider)
            slider.valueChanged.connect(self.resize_tile)
        layout.addLayout(sizes)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.resize_tile()

    def resize_tile(self):
        self.setFixedSize(self.width_slider.value(), self.height_slider.value())
        if self.board.settings:
            for slider, title in ((self.width_slider, "Widget width"), (self.height_slider, "Widget height")):
                self.board.settings.setValue(f"{self.board.prefix}/{self.key}/{title}", slider.value())

    def dragEnterEvent(self, event):
        source = event.source()
        if isinstance(source, MoveHandle) and source.parent().board is self.board:
            event.acceptProposedAction()

    def dropEvent(self, event):
        source = event.source()
        if isinstance(source, MoveHandle) and source.parent().board is self.board:
            self.board.move_before(source.parent().key, self.key)
            event.acceptProposedAction()


class WidgetBoard(QWidget):
    def __init__(self, settings=None, prefix="widgets", columns=2):
        super().__init__()
        self.settings, self.prefix, self.columns = settings, prefix, columns
        self.tiles = {}
        saved = settings.value(f"{prefix}/order", []) if settings else []
        self.order = list(saved) if isinstance(saved, (list, tuple)) else []
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

    def add(self, key, content, width=420, height=380):
        tile = WidgetTile(self, key, content, width, height)
        self.tiles[key] = tile
        if key not in self.order:
            self.order.append(key)
        self.relayout()
        return tile

    def relayout(self):
        for tile in self.tiles.values():
            self.grid.removeWidget(tile)
        visible = [key for key in self.order if key in self.tiles]
        for index, key in enumerate(visible):
            self.grid.addWidget(self.tiles[key], index // self.columns, index % self.columns)
        if self.settings:
            self.settings.setValue(f"{self.prefix}/order", self.order)

    def move(self, key, offset):
        index = self.order.index(key)
        target = max(0, min(len(self.order)-1, index + offset))
        self.order[index], self.order[target] = self.order[target], self.order[index]
        self.relayout()

    def move_before(self, key, target):
        if key == target or key not in self.tiles or target not in self.tiles:
            return
        self.order.remove(key)
        self.order.insert(self.order.index(target), key)
        self.relayout()
