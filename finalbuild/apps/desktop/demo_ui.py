"""Native panels following the supplied automotive dashboard reference.

All counts and diagnostic conclusions come from the active backend session.
"""
from __future__ import annotations

import html
import json
import math
from collections import defaultdict

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QGroupBox, QProgressBar, QListWidget, QListWidgetItem, QPlainTextEdit,
    QLineEdit, QFileDialog, QComboBox, QLayout,
)

from .edge_resize import EdgeResizablePanel
from .channel_labels import CHANNEL_LABELS
from .models import Session, Vehicle, user_report_data
from .vehicle_artwork import load_backend_portrait, NeonVehiclePreview


class Panel(QGroupBox):
    def __init__(self, title=""):
        super().__init__(title)
        self.body = QVBoxLayout(self)
        self.body.setSpacing(12)
        self.body.setContentsMargins(18, 22, 18, 16)


def label(text, role="", wrap=False):
    result = QLabel(text)
    result.setObjectName(role)
    result.setWordWrap(wrap)
    return result


def action(text, callback, primary=False):
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    if primary:
        button.setObjectName("primary")
    button.clicked.connect(callback)
    return button


class CountCard(Panel):
    def __init__(self, title, value="—", accent="blue"):
        super().__init__(title)
        self.setMaximumHeight(120)
        self.value = label(value, "metricValue")
        self.value.setProperty("accent", accent)
        self.body.addWidget(self.value)

    def set_value(self, value):
        self.value.setText(str(value))


class Trace(QWidget):
    """A single channel; independent samples are never mixed into one chart."""
    def __init__(self, color="#20B9FF"):
        super().__init__()
        self.values = []
        self.empty_text = "No samples"
        self.color = color
        self.setMinimumHeight(70)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(3, 6, -3, -6)
        surface = QLinearGradient(r.topLeft(),r.bottomRight())
        surface.setColorAt(0,QColor("#16304B")); surface.setColorAt(1,QColor("#040C19"))
        p.setBrush(QBrush(surface)); p.setPen(QPen(QColor("#345D7B"),1)); p.drawRoundedRect(r,7,7)
        p.setPen(QPen(QColor("#1B4660"), 1))
        for i in range(1, 4):
            y = r.top() + r.height() * i / 4
            p.drawLine(r.left(), int(y), r.right(), int(y))
        if len(self.values) < 2:
            p.setPen(QColor("#839EB3"))
            p.drawText(r, Qt.AlignCenter, self.empty_text)
            return
        low, high = min(self.values), max(self.values)
        padding = max((high - low) * 0.1, abs(high) * 0.01, 1.0)
        low -= padding
        high += padding
        span = high - low
        p.setPen(QPen(QColor(self.color), 2))
        for i in range(1, len(self.values)):
            x1 = r.left() + r.width() * (i - 1) / (len(self.values) - 1)
            x2 = r.left() + r.width() * i / (len(self.values) - 1)
            y1 = r.bottom() - (self.values[i - 1] - low) / span * r.height()
            y2 = r.bottom() - (self.values[i] - low) / span * r.height()
            for thickness, alpha in [(7,30),(4,65),(2,255)]:
                color=QColor(self.color); color.setAlpha(alpha)
                p.setPen(QPen(color,thickness)); p.drawLine(int(x1),int(y1),int(x2),int(y2))


class AnalogGauge(QWidget):
    """Presentation scale only, never a diagnostic threshold or redline."""
    def __init__(self, color):
        super().__init__()
        self.color = color
        self.value = None
        self.unit = ""
        self.channel = ""
        self.setMinimumHeight(160)

    def scale(self):
        return {"rpm": (0, 8000), "C": (-40, 160), "°C": (-40, 160),
                "°F": (-40, 320), "km/h": (0, 260), "mph": (0, 160),
                "%": (0, 100)}.get(self.unit, (0, max(100, (self.value or 0) * 1.2)))

    def bands(self):
        """Visual reference bands, not manufacturer diagnostic limits."""
        low, high = self.scale()
        coolant = self.channel.lower() in {"coolant", "coolant temperature", "coolant_temp", "0x05", "0105", "coolant_c", "coolant_temp_c"}
        if coolant and self.unit in {"C", "°C", "°F"}:
            boundaries = [60, 92, 102, 110]
            if self.unit == "°F":
                boundaries = [value * 1.8 + 32 for value in boundaries]
        else:
            boundaries = [low + (high-low)*fraction for fraction in (.25, .45, .7, .85)]
        edges = [low, *boundaries, high]
        return list(zip(edges, edges[1:], ["#249BFF", "#29CED3", "#35CF87", "#FFBD45", "#FF5367"]))

    def value_color(self):
        bands = self.bands()
        if self.value is not None and bands[2][0] <= self.value <= bands[2][1]:
            return bands[2][2]
        for start, end, color in bands:
            if self.value is not None and self.value < end:
                return color
        return self.bands()[-1][2]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        size = min(self.width() - 72, self.height() - 52)
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = max(10, size / 2)
        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        dial = QRadialGradient(center, radius+10)
        dial.setColorAt(0,QColor("#1B3652")); dial.setColorAt(.78,QColor("#07121E")); dial.setColorAt(.9,QColor("#304B66")); dial.setColorAt(1,QColor("#07111E"))
        p.setBrush(QBrush(dial)); p.setPen(QPen(QColor("#559CC6"),2))
        p.drawEllipse(center,radius+9,radius+9)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#294563"), 9))
        p.drawArc(rect, -45 * 16, 270 * 16)
        low, high = self.scale()
        for start, end, color in self.bands():
            p.setPen(QPen(QColor(color), 9))
            p.drawArc(rect, round((225-270*(end-low)/(high-low))*16), round(270*(end-start)/(high-low)*16))
        if self.channel.lower() in {"coolant", "coolant temperature", "coolant_temp", "0x05", "0105", "coolant_c", "coolant_temp_c"}:
            reference = "197.6–215.6 °F" if self.unit == "°F" else "92–102 °C"
            p.setPen(QColor("#35CF87"))
            p.drawText(QRectF(0, self.height()-22, self.width(), 20), Qt.AlignCenter, reference)
        for i in range(9):
            angle = math.radians(225 - 270 * i / 8)
            def point(r):
                return QPointF(center.x() + r * math.cos(angle), center.y() - r * math.sin(angle))
            p.setPen(QPen(QColor("#829EB8"), 2))
            p.drawLine(point(radius - 8), point(radius - 16))
            pos = point(radius + 15)
            p.drawText(QRectF(pos.x()-24, pos.y()-9, 48, 18), Qt.AlignCenter, f"{low+(high-low)*i/8:g}")
        if self.value is None:
            return
        fraction = max(0, min(1, (self.value-low)/(high-low)))
        angle = math.radians(225 - fraction * 270)
        p.setPen(QPen(QColor(self.value_color()), 4))
        p.drawLine(center, QPointF(center.x() + (radius-20)*math.cos(angle), center.y()-(radius-20)*math.sin(angle)))
        hub = QRadialGradient(center,7); hub.setColorAt(0,QColor("#ECFAFF")); hub.setColorAt(.4,QColor(self.value_color())); hub.setColorAt(1,QColor("#091523"))
        p.setBrush(QBrush(hub)); p.setPen(QPen(QColor("#78C9EF"),1)); p.drawEllipse(center,7,7)


class SignalCard(EdgeResizablePanel):
    def __init__(self, name, color):
        super().__init__(name)
        self.body = QVBoxLayout(self)
        self.body.setSpacing(12)
        self.body.setContentsMargins(18, 22, 18, 16)
        self.default_unit = {"RPM": "rpm", "Coolant temperature": "C", "MAP pressure": "kPa", "O2 sensor": "V"}.get(name, "")
        self.value = label("—", "signalValue")
        self.body.addWidget(self.value)
        self.gauge = AnalogGauge(color)
        self.gauge.unit = self.default_unit
        self.gauge.channel = name
        self.body.addWidget(self.gauge)
        self.trace = Trace(color)
        self.body.addWidget(self.trace)
        self.display_mode = None
        self.set_display_mode("analog")

    def set_display_mode(self, mode):
        mode = mode if mode in {"analog", "chart"} else "analog"
        if mode == self.display_mode:
            return
        self.display_mode = mode
        analog = mode == "analog"
        self.gauge.setVisible(analog)
        self.trace.setVisible(not analog)
        self.ensure_readable_size()

    def set_samples(self, rows):
        values = [float(row["numeric_value"]) for row in rows if row.get("numeric_value") is not None]
        unit = (rows[-1].get("unit") or "") if rows else self.default_unit
        self.value.setText(f"{values[-1]:g} {unit}" if values else "—")
        self.gauge.value = values[-1] if values else None
        self.gauge.unit = unit
        self.gauge.update()
        self.trace.values = values[-90:]
        self.trace.update()


class SignalGrid(QWidget):
    def __init__(self, settings=None, prefix="dashboard"):
        super().__init__()
        self.settings = settings
        self.prefix = prefix
        self.groups = {}
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSizeConstraint(QLayout.SetMinimumSize)
        self.cards, self.selectors = [], []
        self._columns = 0
        self.add_button = action("+ Add widget", self.add_widget)
        for name in ["RPM", "Coolant temperature", "MAP pressure", "O2 sensor"]:
            self._new_card(name)
        self.grid.addWidget(self.add_button, 2, 0, 1, 2)
        self.add_button.setEnabled(False)
        self._arrange_cards()

    def resizeEvent(self,event):
        super().resizeEvent(event); self._arrange_cards()

    def _arrange_cards(self,force=False):
        columns=1 if self.width()<640 else 2
        if columns==self._columns and not force: return
        self._columns=columns
        for card in self.cards: self.grid.removeWidget(card)
        self.grid.removeWidget(self.add_button)
        self.grid.setColumnStretch(0,1); self.grid.setColumnStretch(1,int(columns==2))
        for index,card in enumerate(self.cards): self.grid.addWidget(card,index//columns,index%columns)
        self.grid.addWidget(self.add_button,(len(self.cards)+columns-1)//columns,0,1,columns)

    def _new_card(self, name):
        index = len(self.cards)
        card = SignalCard(name, ["#19B9FF", "#FF5D79", "#B67CFF", "#21D6A0"][index % 4])
        selector = QComboBox()
        selector.setAccessibleName("Telemetry channel")
        selector.setMinimumHeight(34)
        card.body.insertWidget(0, selector)
        card.set_display_mode(self.settings.value("telemetry_display_mode", "analog") if self.settings else "analog")
        card.ensure_readable_size()
        if self.settings:
            card.restore_size(self.settings.value(f"{self.prefix}_edge_size_{index}"))
            card.size_saved.connect(lambda size, i=index: self.settings.setValue(f"{self.prefix}_edge_size_{i}", size))
        selector.currentIndexChanged.connect(self._update_cards)
        self.cards.append(card)
        self.selectors.append(selector)
        self.grid.addWidget(card, index // 2, index % 2)

    def apply_display_mode(self):
        mode = self.settings.value("telemetry_display_mode", "analog") if self.settings else "analog"
        for card in self.cards:
            card.set_display_mode(mode)

    def set_records(self, records):
        self.apply_display_mode()
        groups = defaultdict(list)
        for record in records:
            if record.get("numeric_value") is not None:
                groups[str(record.get("pid") or record.get("channel") or "Unknown channel")].append(record)
        self.groups = groups
        self.channel_labels = {key: (rows[-1].get("display_name") or rows[-1].get("metadata", {}).get("display_name") or CHANNEL_LABELS.get(key.casefold(), key)) for key, rows in groups.items()}
        names = [name for name in getattr(self, "_channel_names", []) if name in groups]
        names += [name for name in groups if name not in names]
        signature = (tuple(names), tuple(self.channel_labels.items()), len(self.selectors))
        if signature == getattr(self, "_channel_signature", None):
            self._update_cards()
            return
        self._channel_names = names
        self._channel_signature = signature
        used = set()
        for i, selector in enumerate(self.selectors):
            previous = selector.currentData()
            saved = self.settings.value(f"{self.prefix}_channel_{i}", "") if self.settings else ""
            selected = next((x for x in [previous, saved, *names] if x in groups and x not in used), "")
            used.add(selected)
            selector.blockSignals(True)
            selector.clear()
            selector.addItem("No samples", "")
            for name in names:
                selector.addItem(self.channel_labels.get(name, name), name)
            selector.setCurrentIndex(max(0, selector.findData(selected)))
            selector.blockSignals(False)
        self._update_cards()

    def _update_cards(self, *_args):
        selected = []
        for i, (selector, card) in enumerate(zip(self.selectors, self.cards)):
            channel = selector.currentData() or ""
            if channel:
                selected.append(channel)
                card.setTitle(self.channel_labels.get(channel, channel))
                if self.settings and self.settings.value(f"{self.prefix}_channel_{i}", "") != channel:
                    self.settings.setValue(f"{self.prefix}_channel_{i}", channel)
            card.gauge.channel = channel or ""
            card.set_samples(self.groups.get(channel, []))
        self.add_button.setEnabled(any(name not in selected for name in self.groups))

    def add_widget(self):
        selected = {s.currentData() for s in self.selectors}
        available = next((name for name in self.groups if name not in selected), None)
        if available is None:
            return
        records = [row for group in self.groups.values() for row in group]
        self.grid.removeWidget(self.add_button)
        self._new_card(available)
        self.set_records(records)
        self.selectors[-1].setCurrentIndex(self.selectors[-1].findData(available))
        self._arrange_cards(force=True)


class DemoDashboard(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(label("Home / Summary", "title"))
        columns = QHBoxLayout()
        left, right = QVBoxLayout(), QVBoxLayout()
        columns.addLayout(left, 5)
        columns.addLayout(right, 4)
        hero = Panel("Selected vehicle")
        self.model_artwork = NeonVehiclePreview()
        self.model_artwork.setMinimumHeight(195)
        hero.body.addWidget(self.model_artwork)
        self.vehicle_name = label("Select a vehicle", "heroTitle")
        self.vehicle_info = label("—", "muted", True)
        hero.body.addWidget(self.vehicle_name)
        hero.body.addWidget(self.vehicle_info)
        hero.body.addWidget(action("Select vehicle  →", lambda: app.navigate_page(1)))
        left.addWidget(hero)
        counts = QHBoxLayout()
        self.dtcs = CountCard("DTC", "0", "red")
        self.results = CountCard("Recorded tests", "0", "green")
        self.ai = CountCard("Hypotheses", "0", "violet")
        for card in (self.dtcs, self.results, self.ai):
            counts.addWidget(card)
        left.addLayout(counts)
        quick = Panel("Quick actions")
        buttons = QGridLayout()
        for i, (name, page) in enumerate([
            ("⚠  DTC list & details", 7), ("▥  Live Data", 4),
            ("✓  Guided Tests", 6), ("◈  AI Analysis", 8),
        ]):
            buttons.addWidget(action(name, lambda _=False, p=page: app.navigate_page(p)), i // 2, i % 2)
        quick.body.addLayout(buttons)
        left.addWidget(quick)
        live = Panel("Live Data / Custom dashboard")
        self.signals = SignalGrid(app.settings_store)
        live.body.addWidget(self.signals)
        self.source = label("No acquisition running", "muted", True)
        live.body.addWidget(self.source)
        live.body.addWidget(action("Open live channels  →", lambda: app.navigate_page(4)))
        right.addWidget(live)
        progress = Panel("Testing progress")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress_text = label("No recommended tests yet", "muted", True)
        progress.body.addWidget(self.progress)
        progress.body.addWidget(self.progress_text)
        right.addWidget(progress)
        layout.addLayout(columns)
        status = QHBoxLayout()
        self.backend = CountCard("Backend", "OFFLINE")
        self.vehicle = CountCard("Vehicle")
        self.vehicle.value.setObjectName("vehicleMetricValue")
        self.session = CountCard("Session")
        self.ecus = CountCard("ECUs")
        for card in (self.backend, self.vehicle, self.session, self.ecus):
            status.addWidget(card)
        layout.addLayout(status)
        self.refresh_btn = action("Refresh status", app.refresh_all)
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignLeft)
        self.refresh()

    def refresh(self):
        app = self.app
        v = app.active_vehicle
        load_backend_portrait(self.model_artwork, app.api.base_url, v.make if v else "", v.model if v else "", v.chassis if v else "", 520, 220)
        self.vehicle_name.setText(f"{v.make} {v.model}" if v else "Select a vehicle")
        self.vehicle_info.setText("  •  ".join(str(x) for x in [v.chassis, v.year, v.engine, "/".join(v.fuel)] if x) if v else "Choose your model to begin a diagnostic session")
        data = app.session_json
        self.dtcs.set_value(len(data.get("dtcs", [])))
        self.results.set_value(len(data.get("test_results", [])))
        self.ai.set_value(len(data.get("hypotheses", [])))
        candidates = app.decision.get("candidates", data.get("recommendations", []))
        latest = {r.get("test_id"): r.get("result") for r in data.get("test_results", [])}
        completed = {tid for tid, result in latest.items() if result in {"PASS", "FAIL"}}
        ids = {r.get("id") or r.get("test_id") for r in candidates}
        done = len(completed & ids)
        self.progress.setValue(round(100 * done / len(ids)) if ids else 0)
        self.progress_text.setText(f"{done}/{len(ids)} tests completed • INCOMPLETE results remain open" if ids else "No recommended tests yet")
        self.backend.set_value("ONLINE" if app.online else "OFFLINE")
        self.vehicle.set_value(f"{v.make} {v.model}" if v else "—")
        self.session.set_value(app.tr_text(app.session.state) if app.session else "—")
        self.ecus.set_value(str(len(app.network.get("ecus", []))) if app.network else "—")
        live = app.pages[4] if len(app.pages) > 4 else None
        from .measurement_units import display_records
        self.signals.set_records(display_records(live._records_data if live else [], app.settings_store.value("unit_system", "metric") == "us"))
        records = live._records_data if live else []
        simulated = any("simulat" in str(r.get("source_type", "")).lower() or r.get("metadata", {}).get("adapter") == "simulator" for r in records)
        self.source.setText("Simulator / synthetic data" if simulated else ("Acquisition samples • see Live Data for connection status" if records else "No acquisition samples"))


class DTCPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        layout.addWidget(label("DTC list & details", "title"))
        layout.addWidget(label("Reported codes are evidence, not a confirmed component failure.", "muted", True))
        self.list = QListWidget()
        layout.addWidget(self.list)
        layout.addWidget(action("Add symptoms / DTC  →", lambda: app.navigate_page(11), True))

    def refresh(self):
        self.list.clear()
        for dtc in self.app.session_json.get("dtcs", []):
            self.list.addItem(f"⚠  {dtc.get('code', '')}\n{dtc.get('description') or 'No description supplied'}\nSource: {dtc.get('source', '—')}")
        if not self.list.count():
            self.list.addItem("No DTCs recorded in the current session")


class HypothesesPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        layout.addWidget(label("AI hypotheses", "title"))
        layout.addWidget(label("Evidence-based hypotheses • Scores are not failure probabilities", "muted", True))
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.missing = QPlainTextEdit()
        self.missing.setReadOnly(True)
        self.missing.setMaximumHeight(140)
        layout.addWidget(self.missing)
        layout.addWidget(action("Recommended tests  →", lambda: app.navigate_page(6), True))

    def refresh(self):
        self.list.clear()
        for i, item in enumerate(self.app.session_json.get("hypotheses", [])):
            score = item.get("confidence_score")
            score_text = f" • evidence score {float(score):.2f}" if isinstance(score, (int, float)) else ""
            self.list.addItem(f"{i + 1}. {item.get('category', 'Hypothesis')}{score_text}\n{item.get('statement', '')}\n{item.get('status', 'unconfirmed')}")
        if not self.list.count():
            self.list.addItem("Add evidence and analyze the session to generate hypotheses")
        questions = self.app.decision.get("missing_questions", []) + self.app.decision.get("questions", [])
        self.missing.setPlainText("\n".join(str(q.get("question", q)) if isinstance(q, dict) else str(q) for q in questions) or "Missing evidence and questions will appear here")


class ReportsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        layout.addWidget(label("Reports / History", "title"))
        layout.addWidget(label("Export the current diagnostic record or reopen a backend session.", "muted", True))
        self.history = QListWidget()
        layout.addWidget(self.history)
        bar = QHBoxLayout()
        bar.addWidget(action("Refresh history", self.load))
        bar.addWidget(action("Open selected", self.open_selected))
        bar.addWidget(action("Export current report", self.export, True))
        from .client_workspace import export_backend_report, tr
        for format in ('pdf', 'json'):
            button = action(tr(app,"Backend report","Отчёт сервера","Backend հաշվետվություն") + ' ' + format.upper(), lambda checked=False, fmt=format: export_backend_report(app, fmt))
            bar.addWidget(button)
        layout.addLayout(bar)
        self.history.itemDoubleClicked.connect(lambda _: self.open_selected())

    def refresh(self):
        if hasattr(self, "_sessions"):
            self.loaded(self._sessions)

    def load(self):
        self.app.run_worker(self.app.api.list_sessions, self.loaded)

    def loaded(self, sessions):
        self._sessions = sessions
        signature = (getattr(self.app, "language", "en"), json.dumps(sessions, sort_keys=True, default=str))
        if signature == getattr(self, "_history_signature", None):
            return
        self._history_signature = signature
        current = self.history.currentItem()
        selected = current.data(Qt.UserRole) if current else None
        self.history.clear()
        for session in sessions:
            v = session.get("vehicle") or {}
            result_label = self.app.tr_text("results")
            item = QListWidgetItem(f"{v.get('make', '')} {v.get('model', '')} • {self.app.tr_text(session.get('state', ''))}\n{len(session.get('dtcs', []))} DTC / {len(session.get('test_results', []))} {result_label}")
            item.setData(Qt.UserRole, session["session_id"])
            self.history.addItem(item)
            if session["session_id"] == selected:
                self.history.setCurrentItem(item)

    def open_selected(self):
        item = self.history.currentItem()
        if item:
            self.app.run_worker(lambda: self.app.api.get_session(item.data(Qt.UserRole), language=self.app.language), self.opened)

    def opened(self, data):
        v = Vehicle.from_json(data["vehicle"]) if data.get("vehicle") else None
        self.app.session = Session(data["session_id"], data["state"], v)
        self.app.active_vehicle = v
        self.app.session_json = data
        self.app.telemetry = {}
        self.app.network = {}
        self.app.active_network = {}
        live = self.app.pages[4]
        live.timer.stop()
        live._records_data = []
        live._status_data = {}
        self.app.decision = {"candidates": data.get("recommendations", [])}
        self.app.refresh_pages()
        self.app.navigate_page(8)

    def export(self):
        data = self.app.session_json
        if not data:
            self.app.show_error("Open a diagnostic session before exporting a report.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, self.app.tr_text("Export diagnostic report"), "diagnostic-report.pdf", "PDF (*.pdf);;Printable HTML (*.html);;Session JSON (*.json)")
        if filename:
            from pathlib import Path
            content = json.dumps(user_report_data(data), ensure_ascii=False, indent=2)
            if not filename.lower().endswith(".json"):
                content = '<!doctype html><meta charset="utf-8"><title>' + html.escape(self.app.tr_text('Diagnostic report')) + '</title><h1>AI Car Scanner</h1><p>' + html.escape(self.app.tr_text('Hypotheses require test confirmation.')) + '</p><pre>' + html.escape(content) + '</pre>'
            if filename.lower().endswith(".pdf"):
                from shared.reporting import render_diagnostic_pdf
                try:
                    Path(filename).write_bytes(render_diagnostic_pdf(user_report_data(data), self.app.language))
                except Exception as exc:
                    self.app.show_error(str(exc))
                    return
            else:
                Path(filename).write_text(content, encoding="utf-8")
            self.app.statusBar().showMessage(self.app.tr_text("Diagnostic report exported"))


class TeachPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        layout.addWidget(label("Teach AI / Your solution", "title"))
        layout.addWidget(label("Record an observed repair and its evidence. Ingestion adds reference material; it does not train the model or confirm a diagnosis.", "muted", True))
        self.title = QLineEdit(str(app.settings_store.value("case_note_title", "")))
        self.title.setPlaceholderText("Repair / observation title")
        self.note = QPlainTextEdit(str(app.settings_store.value("case_note", "")))
        self.note.setPlaceholderText("Vehicle, DTCs, measurements, repair, and verified outcome…")
        self.result = label("Drafts stay on this device until you choose to ingest them.", "muted", True)
        layout.addWidget(self.title)
        layout.addWidget(self.note)
        bar = QHBoxLayout()
        bar.addWidget(action("Save draft", self.save))
        bar.addWidget(action("Ingest reference note", self.ingest, True))
        layout.addLayout(bar)
        layout.addWidget(self.result)

    def refresh(self):
        pass

    def save(self):
        self.app.settings_store.setValue("case_note_title", self.title.text())
        self.app.settings_store.setValue("case_note", self.note.toPlainText())
        self.result.setText(self.app.tr_text("Draft saved on this device"))

    def ingest(self):
        if not self.title.text().strip() or not self.note.toPlainText().strip():
            self.app.show_error("Add a title and observed repair details first.")
            return
        self.save()
        title, text = self.title.text().strip(), self.note.toPlainText().strip()
        self.app.run_worker(lambda: self.app.api.ingest_reference(title, text), lambda result: self.result.setText(self.app.tr_text(f"Reference processed: {len(result.get('chunks', []))} chunks. No model training performed.")))
