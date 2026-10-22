from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QWidget

from apps.desktop.models import Session, Vehicle
from PIL import Image, ImageChops

from apps.desktop.stage_windows_icons import stage_icons
from apps.desktop.ui import (
    DashboardPage,
    DevicesPage,
    DiagnosticPage,
    LiveDataPage,
    MainWindow,
    MetricCard,
    NetworkPage,
    Sparkline,
    TestsPage as DiagnosticTestsPage,
    VehicleDialog,
    VehiclesPage,
    _translate_ui_text,
    _translate_ui_block,
)


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    # Destroy Qt widgets before Python tears down their application/callbacks.
    import gc
    from PySide6.QtCore import QCoreApplication, QEvent
    for widget in app.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    gc.collect()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


class FakeApp:
    def __init__(self):
        self.settings_store = Mock()
        self.settings_store.value.return_value = ""
        self.pages = []
        self.nav = Mock()
        self.online = True
        self.active_vehicle = Vehicle("Mercedes-Benz", "E-Class", "W211", 2006, "M272", ["petrol", "lpg"], "ME9.7")
        self.session = Session("session-123456", "ANALYSIS_READY", self.active_vehicle)
        self.session_json = {
            "state": "ANALYSIS_READY",
            "evidence": [{"status": "reported", "fact": "LPG-only misfire", "source": "driver"}],
            "hypotheses": [{"category": "LPG delivery", "statement": "Check injector balance", "status": "possible"}],
        }
        self.decision = {"missing_questions": ["Does it happen on petrol?"], "questions": [{"question": "What is fuel pressure?"}], "candidates": [
            {"id": "test-1", "name": "Check LPG pressure", "purpose": "Verify delivery", "priority_score": 0.8, "risk": "LOW"}
        ]}
        self.telemetry = {"signals": [{"pid": "RPM", "count": 4, "min_value": 700, "max_value": 2100, "mean": 1200, "event_count": 2}]}
        self.network = {"ecus": [{"ecu_id": "ME9.7", "bus": "CAN", "state": "INFERRED", "confidence": 0.7}]}
        self.active_network = {"responding": ["ME9.7"]}
        self.devices = [{
            "device_id": "dev-1", "status": "connected", "connection_type": "Wi-Fi",
            "manufacturer": "Generic", "model": "ELM327", "protocol": "CAN",
            "firmware_version": "1.5", "capabilities": {"dtc": True},
            "metadata": {"host": "192.0.2.10", "port": 35000},
        }]
        self.selected_device_id = "dev-1"
        self.vehicles = [self.active_vehicle]
        self.test_candidates = []
        self.api = Mock()
        self.api.acquisition_status.return_value = {"state": "STOPPED"}
        self.api.ai_provider_info.return_value = {"available": False, "model": "local", "reason": "model offline"}
        self.api.acquisition_records.return_value = {"records": [{"numeric_value": 1.2}, {"numeric_value": None}]}

    def tr_text(self, text): return _translate_ui_text(text, "en")
    def refresh_all(self): pass
    def add_vehicle(self): pass
    def delete_selected_vehicle(self): pass
    def new_session(self): pass
    def analyze_input(self): pass
    def start_simulator(self): pass
    def stop_simulator(self): pass
    def analyze_telemetry(self): pass
    def ai_analyze_live_data(self): pass
    def record_selected_test(self): pass
    def scan_devices(self, _transport): pass
    def add_simulator_device(self): pass
    def probe_wifi(self): pass
    def connect_selected_device(self): pass
    def disconnect_selected_device(self): pass
    def reconnect_selected_device(self): pass
    def read_device_vin(self): pass
    def read_device_dtcs(self): pass
    def read_device_live_data(self): pass
    def refresh_network(self): pass
    def active_probe(self): pass
    def refresh_telemetry(self): pass



def test_ui_translation_covers_pages_and_switches_languages(qapp):
    assert _translate_ui_text("Dashboard", "ru") == "Обзор"
    assert _translate_ui_text("Dashboard", "hy") == "Գլխավոր"
    assert _translate_ui_text("Session state: ANALYSIS_READY", "ru").startswith("Состояние сеанса:")
    russian = _translate_ui_text("Session state: ANALYSIS_READY", "ru")
    armenian = _translate_ui_text(russian, "hy")
    assert armenian.startswith("Սեսիայի վիճակ՝")
    assert _translate_ui_text(russian, "en") == "Session state: ANALYSIS_READY"
    assert _translate_ui_text("PASS", "ru") == "Пройден"
    assert _translate_ui_text("FAIL", "hy") == "Չանցավ"
    assert _translate_ui_text("INCOMPLETE", "hy") == "Անորոշ"
    assert _translate_ui_block("Model: Tesla Model S", "ru") == "Модель: Tesla Model S"

def test_desktop_icon_stage_preserves_input_and_generates_matching_formats(tmp_path):
    """Build-time artwork must never overwrite a locally edited icon."""
    source = tmp_path / "edited-desktop-icon.png"
    Image.new("RGBA", (512, 512), (20, 90, 140, 255)).save(source, format="PNG")
    before = source.read_bytes()

    staged = tmp_path / "staged"
    stage_icons(source, staged)

    assert source.read_bytes() == before
    with Image.open(source) as original, Image.open(staged / "AI-Car-Scanner.webp") as webp:
        assert webp.format == "WEBP"
        assert webp.size == original.size
        assert ImageChops.difference(
            original.convert("RGBA"), webp.convert("RGBA")
        ).getbbox() is None

    with Image.open(staged / "AI-Car-Scanner-mobile.png") as png:
        assert png.format == "PNG"
        assert png.size == (512, 512)

    with Image.open(staged / "AI-Car-Scanner.ico") as ico:
        assert ico.format == "ICO"
        assert (256, 256) in ico.ico.sizes()


def test_sparkline_limits_values_and_paints(qapp):
    chart = Sparkline([1, 2])
    chart.set_values(list(range(150)))
    assert chart.values == list(range(30, 150))
    chart.resize(320, 100)
    image = QImage(chart.size(), QImage.Format.Format_ARGB32)
    chart.render(image)
    chart.set_values([5, 5, 5])
    chart.render(image)
    chart.set_values([])
    chart.render(image)
    assert chart.values == []


def test_metric_card_updates_displayed_value(qapp):
    card = MetricCard("Backend", "OFFLINE")
    assert card.title() == "Backend"
    assert card.value.text() == "OFFLINE"
    card.set_value("ONLINE")
    assert card.value.text() == "ONLINE"


def test_vehicle_dialog_fallback_and_vehicle_conversion(qapp):
    dialog = VehicleDialog()
    # The bundled offline catalog should expose all eight supported makes.
    assert dialog.make.count() == 8
    assert dialog.make.currentText() == "Mercedes-Benz"
    assert dialog.model.currentText() == "E-Class"
    assert dialog.chassis.currentText() == "W211"
    assert dialog.year.currentText() == "2006"
    dialog.fuel.setText("Petrol, LPG, ,")
    vehicle = dialog.vehicle()
    assert vehicle.make == "Mercedes-Benz"
    assert vehicle.year == 2006
    assert vehicle.fuel == ["Petrol", "LPG"]


def test_vehicle_dialog_filters_catalog_and_selects_matching_vehicle(qapp):
    parent = QWidget()
    parent.api = SimpleNamespace(vehicle_catalog_entries=lambda: [
        {"make": "Kia", "model": "Forte", "chassis": "BD", "year": 2017, "engine": "2.0", "ecu": "SIM2K"},
        {"make": "Mercedes-Benz", "model": "E-Class", "chassis": "W211", "year": 2006, "engine": "M272 E35 3.5", "ecu": "ME9.7"},
        {"make": "Mercedes-Benz", "model": "E-Class", "chassis": "W212", "year": 2010, "engine": "M272", "ecu": "ME9.7"},
    ])
    dialog = VehicleDialog(parent)
    assert dialog.make.currentText() == "Mercedes-Benz"
    assert dialog.model.currentText() == "E-Class"
    assert dialog.chassis.currentText() == "W211"
    assert dialog.vehicle().ecu == "ME9.7"
    dialog.make.setCurrentText("Kia")
    assert dialog.model.currentText() == "Forte"
    assert dialog.chassis.currentText() == "BD"
    assert dialog.vehicle().year == 2017


def test_vehicle_dialog_handles_catalog_api_failure(qapp):
    parent = QWidget()
    parent.api = SimpleNamespace(vehicle_catalog_entries=Mock(side_effect=RuntimeError("offline")))
    dialog = VehicleDialog(parent)
    assert dialog.make.currentText() == "Mercedes-Benz"
    assert dialog.vehicle().engine == "M272 E35 3.5"


def test_dashboard_refresh_updates_metrics(qapp):
    app = FakeApp()
    page = DashboardPage(app)
    page.refresh()
    assert page.backend.value.text() == "ONLINE"
    assert page.vehicle.value.text() == "Mercedes-Benz E-Class"
    assert page.session.value.text() == "ANALYSIS_READY"
    assert page.ecus.value.text() == "1"
    app.online = False
    app.active_vehicle = None
    app.session = None
    app.network = {}
    page.refresh()
    assert page.backend.value.text() == "OFFLINE"
    assert page.vehicle.value.text() == "—"
    assert page.session.value.text() == "—"


def test_vehicles_page_renders_and_selects_local_vehicles(qapp):
    app = FakeApp()
    page = VehiclesPage(app)
    page.refresh()
    assert page.list.count() == 1
    assert page.delete_btn.isEnabled()
    assert "Mercedes-Benz" in page.details.toPlainText()
    page.list.clearSelection()
    app.vehicles = []
    app.active_vehicle = None
    page.refresh()
    assert page.list.count() == 0
    assert page.details.toPlainText() == ""


def test_diagnostic_page_formats_summary_and_refreshes_session(qapp):
    app = FakeApp()
    page = DiagnosticPage(app)
    assert page.lbl.text() == "No active session"
    page.refresh()
    assert "LPG delivery" in page.summary.toPlainText()
    assert "LPG-only misfire" in page.evidence.toPlainText()
    assert "Check injector balance" in page.hypotheses.toPlainText()
    assert "Does it happen on petrol?" in page.questions.toPlainText()
    assert "hypotheses are not confirmed" in page.summary.toPlainText().lower()
    app.session = None
    page.refresh()
    assert page.lbl.text() == "No active session"


def test_tests_page_builds_candidates_from_decision_payload(qapp):
    app = FakeApp()
    page = DiagnosticTestsPage(app)
    page.refresh()
    assert page.list.count() == 1
    assert app.test_candidates[0].test_id == "test-1"
    assert page.list.item(0).data(256) == "test-1"
    app.decision = {}
    page.refresh()
    assert page.list.count() == 0
    assert app.test_candidates == []



def test_test_result_labels_are_localized_but_keep_canonical_values(qapp):
    app = FakeApp()
    app.language = "ru"
    page = DiagnosticTestsPage(app)
    assert page.result.itemText(0) == "Пройден"
    assert page.result.itemData(0) == "PASS"
    assert page.result.itemText(2) == "Неполно"
    assert page.result.itemData(2) == "INCOMPLETE"

def test_devices_page_refresh_config_and_selection(qapp):
    app = FakeApp()
    page = DevicesPage(app)
    page.refresh()
    assert page.list.count() == 1
    assert page.current()["device_id"] == "dev-1"
    assert page.host.text() == "192.0.2.10"
    config = page.config()
    assert config["port"] == 35000
    assert config["baudrate"] == 115200
    assert config["host"] == "192.0.2.10"
    page.host.setText(" 192.0.2.11 ")
    page.tx_uuid.setText(" tx ")
    assert page.config()["host"] == "192.0.2.11"
    assert page.config()["tx_uuid"] == "tx"
    page.list.clearSelection()
    page.list.setCurrentRow(-1)
    assert page.current() is None


def test_network_page_formats_inferred_and_active_ecus(qapp):
    app = FakeApp()
    page = NetworkPage(app)
    page.refresh()
    text = page.tree.toPlainText()
    assert "ME9.7" in text
    assert "PASSIVE / INFERRED NETWORK" in text
    assert "ACTIVE CORRELATION" in text
    app.network = {}
    app.active_network = None
    page.refresh()
    assert "No discovered ECU candidates" in page.tree.toPlainText()


def test_live_data_page_refresh_does_not_block_on_api_calls(qapp):
    app = FakeApp()
    page = LiveDataPage(app)
    page.refresh()
    assert page.status.text() == "STOPPED"
    assert "OFFLINE" in page.ai_status.text()
    assert page.table.rowCount() == 1
    assert page.chart.values == []
    app.api.acquisition_status.assert_not_called()
    app.api.ai_provider_info.assert_not_called()
    app.api.acquisition_records.assert_not_called()
    assert not page.timer.isActive()


def test_refresh_telemetry_deduplicates_requests_and_discards_stale_sessions():
    old_session = Session("old-session", "ACQUIRING")
    new_session = Session("new-session", "ACQUIRING")
    live_page = SimpleNamespace(_records_data=[])
    app = SimpleNamespace(
        session=old_session,
        api=Mock(),
        pages=[None, None, None, None, live_page],
        telemetry={},
        run_worker=Mock(),
        refresh_pages=Mock(),
        statusBar=Mock(return_value=SimpleNamespace(showMessage=Mock())),
    )

    MainWindow.refresh_telemetry(app)
    worker, done = app.run_worker.call_args.args
    assert app._telemetry_refresh_in_flight is True

    # A timer tick while the first request is active must not start another worker.
    MainWindow.refresh_telemetry(app)
    assert app.run_worker.call_count == 1

    app.api.telemetry_summary.return_value = {"signals": []}
    app.api.acquisition_records.return_value = {"records": [{"numeric_value": 3.5}]}
    result = worker()
    app.session = new_session
    done(result)

    assert app._telemetry_refresh_in_flight is False
    assert app.telemetry == {}
    assert live_page._records_data == []
    app.refresh_pages.assert_not_called()


def test_live_data_poll_ignores_absent_session_and_reports_backend_error(qapp):
    app = FakeApp()
    app.session = None
    page = LiveDataPage(app)

    # With no active session, polling must return without starting a worker.
    page._poll()
    assert page._poll_in_flight is False
    assert app.api.acquisition_status.call_count == 0

    # Use a deterministic synchronous worker in this unit test. The production
    # MainWindow schedules this callback on its worker pool.
    app.run_worker = lambda worker, done: done(worker())
    app.session = Session("s-2", "CREATED")
    app.online = True
    app.api.acquisition_status.side_effect = RuntimeError("backend unavailable")

    page._poll()

    assert page._poll_in_flight is False
    assert page.status.text() == "Acquisition unavailable"
    assert not page.timer.isActive()


def test_diagnostic_summary_empty_hypotheses_are_explicit():
    summary = DiagnosticPage._summary_text({"state": "COLLECTING_EVIDENCE"}, [])
    assert "No diagnostic hypotheses generated yet." in summary
    assert "not confirmed component failures" in summary


@pytest.mark.parametrize(
    "error,expected", [
        ("HTTP 404: Acquisition not started", "Acquisition not started"),
        ("HTTP 404: Session not found", "Session not found"),
        ("HTTP 503: service unavailable", "Acquisition unavailable"),
    ],
)
def test_live_data_reports_endpoint_state_not_global_backend_health(qapp, error, expected):
    app = FakeApp()
    app.online = True  # FastAPI /health is independently healthy.
    page = LiveDataPage(app)
    page._details_loaded({
        "status": {"_error": error},
        "provider": {"available": False, "model": "not-loaded"},
        "records": {"records": []},
    })
    assert page.status.text() == expected
    assert page.status.toolTip() == error
    assert app.online is True
    page._poll_done({"_error": error})
    assert page.status.text() == expected
    assert app.online is True
    page.timer.stop()


def test_live_data_backend_offline_status_is_not_mislabeled_as_acquisition(qapp):
    app = FakeApp()
    app.online = False
    page = LiveDataPage(app)
    page._details_loaded({
        "status": {"_error": "connection refused"},
        "provider": {"available": False},
        "records": {"records": []},
    })
    assert page.status.text() == "Backend offline"
    page.timer.stop()


@pytest.mark.parametrize("language", ["hy", "ru"])
def test_acquisition_errors_follow_selected_ui_language(qapp, language):
    app = FakeApp()
    app.tr_text = lambda text: _translate_ui_text(text, language)
    page = LiveDataPage(app)
    page._poll_done({"_error": "HTTP 404: Acquisition not started"})
    assert page.status.text() == _translate_ui_text("Acquisition not started", language)
    assert page.status.text() != "Acquisition not started"
    page.timer.stop()
