"""Page Object Model regression tests for the PySide6 desktop UI.

All backend, persistence and hardware boundaries are replaced with test doubles.
These tests are intended to run locally with:
    QT_QPA_PLATFORM=offscreen python -m pytest -q tests/desktop/test_ui_pom.py
"""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from apps.desktop import ui
from apps.desktop.models import Session, Vehicle


# ----------------------------- Page Object Model -----------------------------

class DashboardPO:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[0]

    def refresh(self):
        self.page.refresh()

    @property
    def backend(self):
        return self.page.backend.value.text()

    @property
    def vehicle(self):
        return self.page.vehicle.value.text()

    @property
    def session(self):
        return self.page.session.value.text()

    @property
    def ecu_count(self):
        return self.page.ecus.value.text()

    def click_refresh(self):
        self.page.refresh_btn.click()


class VehiclesPO:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[1]

    def refresh(self):
        self.page.refresh()

    def select(self, row=0):
        self.page.list.setCurrentRow(row)

    def selected_details(self):
        return self.page.details.toPlainText()

    @property
    def count(self):
        return self.page.list.count()

    @property
    def delete_enabled(self):
        return self.page.delete_btn.isEnabled()


class DiagnosticPO:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[3]

    def enter_symptom(self, text):
        self.page.symptom.setPlainText(text)

    def enter_dtc(self, code):
        self.page.dtc.setText(code)

    def submit(self):
        for button in self.page.findChildren(QPushButton):
            if button.text() in ("Add evidence + Analyze", "Ավելացնել տվյալներ և վերլուծել"):
                button.click()
                return
        raise AssertionError("Analyze button not found")

    def refresh(self):
        self.page.refresh()

    @property
    def summary(self):
        return self.page.summary.toPlainText()

    @property
    def evidence(self):
        return self.page.evidence.toPlainText()

    @property
    def hypotheses(self):
        return self.page.hypotheses.toPlainText()

    @property
    def questions(self):
        return self.page.questions.toPlainText()


class LiveDataPO:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[4]

    def refresh(self):
        self.page.refresh()

    @property
    def status(self):
        return self.page.status.text()

    @property
    def ai_status(self):
        return self.page.ai_status.text()

    @property
    def row_count(self):
        return self.page.table.rowCount()

    @property
    def plotted_values(self):
        return self.page.chart.values

    def stop_timer(self):
        self.page.timer.stop()


class TestsPO:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[6]

    def refresh(self):
        self.page.refresh()

    def select(self, row=0):
        self.page.list.setCurrentRow(row)

    def set_result(self, result):
        index = self.page.result.findData(result)
        assert index >= 0, f"Unknown canonical test result: {result}"
        self.page.result.setCurrentIndex(index)

    def set_notes(self, notes):
        self.page.notes.setText(notes)

    @property
    def count(self):
        return self.page.list.count()

    @property
    def selected_test_id(self):
        item = self.page.list.currentItem()
        return item.data(Qt.UserRole) if item else None

    @property
    def result_code(self):
        return self.page.result.currentData()


class DevicesPO:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[2]

    def refresh(self):
        self.page.refresh()

    def select(self, row=0):
        self.page.list.setCurrentRow(row)

    def configure_wifi(self, host, port):
        self.page.host.setText(host)
        self.page.port.setValue(port)

    def configure_ble(self, tx, rx):
        self.page.tx_uuid.setText(tx)
        self.page.rx_uuid.setText(rx)

    def config(self):
        return self.page.config()

    @property
    def selected_device(self):
        return self.page.current()

    @property
    def result(self):
        return self.page.result.toPlainText()


class NetworkPO:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[5]

    def refresh(self):
        self.page.refresh()

    @property
    def text(self):
        return self.page.tree.toPlainText()


# -------------------------------- Test fixtures ------------------------------

class MemorySettings:
    values = {}

    def __init__(self, *_args):
        self.values = dict(type(self).values)

    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        return type(value) if type is not None and value is not None else value

    def setValue(self, key, value):
        self.values[key] = value


class FakeStore:
    def __init__(self, vehicles=None):
        self.vehicles = list(vehicles or [])
        self.saved = []

    def load(self):
        return list(self.vehicles)

    def save(self, vehicles):
        self.vehicles = list(vehicles)
        self.saved.append(list(vehicles))


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    app.closeAllWindows()
    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


@pytest.fixture
def vehicle():
    return Vehicle("Mercedes-Benz", "E-Class", "W211", 2006, "M272", ["Petrol", "LPG"], "ME9.7")


@pytest.fixture
def fake_api():
    api = Mock()
    api.vehicle_catalog_entries.return_value = [
        {"make": "Mercedes-Benz", "model": "E-Class", "chassis": "W211",
         "year": 2006, "engine": "M272", "ecu": "ME9.7"},
        {"make": "Kia", "model": "Forte", "chassis": "BD",
         "year": 2017, "engine": "2.0", "ecu": "SIM2K"},
    ]
    return api


@pytest.fixture
def window_factory(monkeypatch, qapp, fake_api, vehicle):
    made = []

    def build(vehicles=None):
        store = FakeStore(vehicles if vehicles is not None else [vehicle])
        MemorySettings.values = {"language": "en", "dark_theme": True}
        monkeypatch.setattr(ui, "DiagnosticApiClient", lambda: fake_api)
        monkeypatch.setattr(ui, "VehicleStore", lambda: store)
        monkeypatch.setattr(ui, "QSettings", MemorySettings)
        # Constructor must not initiate HTTP calls or background workers.
        monkeypatch.setattr(ui.MainWindow, "refresh_all", lambda self: None)
        window = ui.MainWindow()
        window._test_store = store
        window.show()
        qapp.processEvents()
        made.append(window)
        return window

    yield build
    for window in made:
        window.close()
        window.deleteLater()
    qapp.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


# --------------------------------- UI tests ----------------------------------

def test_main_window_builds_all_seven_navigation_pages(window_factory):
    window = window_factory()
    assert window.windowTitle() == "AI Auto Diagnostic Workstation"
    assert window.nav.count() == 7
    assert len(window.pages) == 7
    assert window.stack.count() == 1
    assert window.nav.currentRow() == 0
    assert [window.nav.item(i).text().split()[-1] for i in range(window.nav.count())] == [
        "Dashboard", "Vehicles", "Devices", "Diagnostic", "Data", "Network", "Tests"
    ]


def test_navigation_selects_pages_and_live_data_request_is_guarded(window_factory, fake_api):
    window = window_factory()
    window.nav.setCurrentRow(4)
    assert window.nav.currentRow() == 4
    # No active session means the Live Data page must not issue requests.
    assert window.pages[4]._details_in_flight is False
    fake_api.acquisition_status.assert_not_called()


def test_dashboard_page_object_displays_online_vehicle_session_and_ecus(window_factory):
    window = window_factory()
    window.online = True
    window.session = Session("session-123456", "READY", window.active_vehicle)
    window.network = {"ecus": [{"ecu_id": "ME9.7"}, {"ecu_id": "TCM"}]}
    page = DashboardPO(window)
    page.refresh()
    assert page.backend == "ONLINE"
    assert page.vehicle == "Mercedes-Benz E-Class"
    assert page.session == "session-"
    assert page.ecu_count == "2"

    window.online = False
    window.active_vehicle = None
    window.session = None
    window.network = {}
    page.refresh()
    assert (page.backend, page.vehicle, page.session, page.ecu_count) == (
        "OFFLINE", "—", "—", "—"
    )


def test_vehicles_page_object_lists_selects_and_displays_vehicle(window_factory, vehicle):
    window = window_factory(vehicles=[vehicle])
    page = VehiclesPO(window)
    page.refresh()
    assert page.count == 1
    assert page.delete_enabled
    page.select()
    details = page.selected_details()
    assert "Make: Mercedes-Benz" in details
    assert "Chassis: W211" in details
    assert "Engine: M272" in details
    assert "Fuel: Petrol, LPG" in details

    window.vehicles = []
    window.active_vehicle = None
    page.refresh()
    assert page.count == 0
    assert page.selected_details() == ""


def test_vehicle_dialog_page_object_filters_catalog_and_converts_form(qapp, fake_api):
    parent = QWidget()
    parent.api = fake_api
    parent.language = "en"
    dialog = ui.VehicleDialog(parent)
    assert dialog.make.findText("Mercedes-Benz") >= 0
    assert dialog.make.findText("Kia") >= 0
    dialog.make.setCurrentText("Kia")
    assert dialog.model.currentText() == "Forte"
    assert dialog.chassis.currentText() == "BD"
    dialog.fuel.setText("Petrol, LPG, ,")
    vehicle = dialog.vehicle()
    assert (vehicle.make, vehicle.model, vehicle.chassis, vehicle.year) == (
        "Kia", "Forte", "BD", 2017
    )
    assert vehicle.fuel == ["Petrol", "LPG"]
    dialog.close()


def test_diagnostic_page_object_renders_evidence_hypotheses_and_questions(window_factory):
    window = window_factory()
    window.session = Session("session-42", "ANALYSIS_READY", window.active_vehicle)
    window.session_json = {
        "state": "ANALYSIS_READY",
        "evidence": [{"status": "reported", "fact": "LPG-only misfire", "source": "driver"}],
        "hypotheses": [{"category": "LPG delivery", "statement": "Check injectors", "status": "possible"}],
    }
    window.decision = {
        "missing_questions": ["Does it happen on petrol?"],
        "questions": [{"question": "What is fuel pressure?"}],
    }
    page = DiagnosticPO(window)
    page.refresh()
    assert "ANALYSIS_READY" in page.summary
    assert "hypotheses are not confirmed component failures" in page.summary
    assert "LPG-only misfire" in page.evidence
    assert "LPG delivery" in page.hypotheses
    assert "Does it happen on petrol?" in page.questions
    assert "What is fuel pressure?" in page.questions


def test_diagnostic_empty_hypotheses_are_explicit():
    summary = ui.DiagnosticPage._summary_text({"state": "COLLECTING_EVIDENCE"}, [])
    assert "No diagnostic hypotheses generated yet." in summary
    assert "not confirmed component failures" in summary


def test_live_data_page_object_handles_empty_and_populated_telemetry(window_factory):
    window = window_factory()
    page = LiveDataPO(window)
    page.refresh()
    assert page.status == "STOPPED"
    assert page.row_count == 0
    assert page.plotted_values == []

    window.session = Session("session-live", "ACQUIRING", window.active_vehicle)
    window.telemetry = {"signals": [
        {"pid": "RPM", "count": 2, "min_value": 700, "max_value": 1500, "mean": 1100, "event_count": 1}
    ]}
    window.pages[4]._records_data = [{"numeric_value": 700}, {"numeric_value": None}, {"numeric_value": 1500}]
    page.refresh()
    assert page.row_count == 1
    assert page.page.table.item(0, 0).text() == "RPM"
    assert page.plotted_values == [700.0, 1500.0]
    page.stop_timer()


def test_tests_page_object_keeps_result_codes_canonical(window_factory):
    window = window_factory()
    window.decision = {"candidates": [
        {"id": "test-1", "name": "Check LPG pressure", "purpose": "Verify delivery",
         "priority_score": 0.8, "risk": "LOW"}
    ]}
    page = TestsPO(window)
    page.refresh()
    assert page.count == 1
    assert page.selected_test_id == "test-1"
    page.set_result("FAIL")
    page.set_notes("Pressure below specification")
    assert page.result_code == "FAIL"
    assert page.page.notes.text() == "Pressure below specification"
    page.set_result("INCOMPLETE")
    assert page.result_code == "INCOMPLETE"

    window.decision = {}
    page.refresh()
    assert page.count == 0
    assert window.test_candidates == []


def test_devices_page_object_selects_device_and_builds_connection_config(window_factory):
    window = window_factory()
    window.devices = [{
        "device_id": "dev-wifi", "status": "connected", "connection_type": "Wi-Fi",
        "manufacturer": "Generic", "model": "ELM327", "protocol": "CAN",
        "firmware_version": "1.5", "capabilities": {"dtc": True},
        "metadata": {"host": "192.0.2.10", "port": 35000},
    }]
    window.selected_device_id = "dev-wifi"
    page = DevicesPO(window)
    page.refresh()
    page.select()
    assert page.selected_device["device_id"] == "dev-wifi"
    assert "Generic" in page.page.info_box.toPlainText()
    page.configure_wifi(" 192.0.2.11 ", 35001)
    page.configure_ble(" tx-uuid ", " rx-uuid ")
    assert page.config() == {
        "host": "192.0.2.11", "port": 35001, "baudrate": 115200,
        "tx_uuid": "tx-uuid", "rx_uuid": "rx-uuid",
    }


def test_devices_page_handles_no_selected_device(window_factory):
    window = window_factory()
    page = DevicesPO(window)
    page.refresh()
    page.page.list.setCurrentRow(-1)
    assert page.selected_device is None


def test_network_page_object_formats_passive_and_active_ecu_data(window_factory):
    window = window_factory()
    window.network = {"ecus": [
        {"ecu_id": "ME9.7", "bus": "CAN", "state": "INFERRED", "confidence": 0.7}
    ]}
    window.active_network = {"responding": ["ME9.7"]}
    page = NetworkPO(window)
    page.refresh()
    assert "PASSIVE / INFERRED NETWORK" in page.text
    assert "ME9.7" in page.text
    assert "ACTIVE CORRELATION" in page.text
    window.network = {}
    window.active_network = None
    page.refresh()
    assert "No discovered ECU candidates yet." in page.text


def test_language_switch_translates_window_and_navigation(window_factory):
    window = window_factory()
    window.language = "hy"
    window._apply_language()
    assert window.windowTitle() == ui._translate_ui_text("AI Auto Diagnostic Workstation", "hy")
    assert window.nav.item(0).text().endswith(ui._translate_ui_text("Dashboard", "hy"))


def test_analyze_input_rejects_empty_evidence_and_dtc(window_factory, monkeypatch):
    window = window_factory()
    errors = []
    monkeypatch.setattr(window, "show_error", errors.append)
    window.session = Session("session-1", "READY", window.active_vehicle)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    DiagnosticPO(window).submit()
    assert errors == ["Enter a symptom, observation or DTC."]
    assert jobs == []


def test_analyze_input_worker_sends_symptom_and_dtc(window_factory, monkeypatch, fake_api):
    window = window_factory()
    window.session = Session("session-1", "READY", window.active_vehicle)
    page = DiagnosticPO(window)
    page.enter_symptom("Engine shakes on LPG")
    page.enter_dtc("P0302")
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    page.submit()
    assert len(jobs) == 1
    worker, callback = jobs[0]
    fake_api.ingest_evidence.return_value = {}
    fake_api.add_dtc.return_value = {}
    fake_api.analyze.return_value = {"session_id": "session-1", "state": "ANALYZED"}
    result = worker()
    fake_api.ingest_evidence.assert_called_once_with("session-1", "Engine shakes on LPG")
    fake_api.add_dtc.assert_called_once_with("session-1", "P0302")
    fake_api.analyze.assert_called_once_with("session-1", language="en")
    assert result["state"] == "ANALYZED"
    assert callable(callback)


def test_main_window_selected_device_validation_does_not_start_worker(window_factory, monkeypatch):
    window = window_factory()
    errors = []
    monkeypatch.setattr(window, "show_error", errors.append)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    assert window._selected_device() is None
    assert errors == ["Select a VCI/device first."]
    assert jobs == []


def test_worker_run_emits_success_and_failure_signals(qapp):
    successful = ui.Worker(lambda: {"ok": True})
    success_values = []
    failure_values = []
    successful.finished_ok.connect(success_values.append)
    successful.failed.connect(failure_values.append)
    successful.run()
    assert success_values == [{"ok": True}]
    assert failure_values == []

    def explode():
        raise RuntimeError("controlled worker error")

    failing = ui.Worker(explode)
    failing.finished_ok.connect(success_values.append)
    failing.failed.connect(failure_values.append)
    failing.run()
    assert failure_values == ["controlled worker error"]


def test_sparkline_handles_empty_constant_and_long_series(qapp):
    chart = ui.Sparkline()
    chart.resize(320, 100)
    chart.set_values(list(range(150)))
    assert chart.values == list(range(30, 150))
    chart.show()
    qapp.processEvents()
    chart.set_values([5, 5, 5])
    qapp.processEvents()
    chart.set_values([])
    qapp.processEvents()
    assert chart.values == []
    chart.close()


def test_metric_card_initial_and_updated_values(qapp):
    card = ui.MetricCard("Vehicle", "Mercedes-Benz")
    assert card.title() == "Vehicle"
    assert card.value.text() == "Mercedes-Benz"
    assert card.value.objectName() == "vehicleMetricValue"
    card.set_value("E350")
    assert card.value.text() == "E350"


def test_translation_round_trips_dynamic_session_state_between_languages():
    source = "Session state: ANALYSIS_READY"
    russian = ui._translate_ui_text(source, "ru")
    armenian = ui._translate_ui_text(russian, "hy")
    english = ui._translate_ui_text(armenian, "en")
    assert russian.startswith("Состояние сеанса:")
    assert armenian.startswith("Սեսիայի վիճակ՝")
    assert english == source



def test_new_session_offline_reports_error_without_starting_worker(window_factory, monkeypatch):
    window = window_factory()
    window.online = False
    errors = []
    jobs = []
    monkeypatch.setattr(window, "show_error", errors.append)
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    window.new_session()
    assert errors == ["Backend is offline. Start the FastAPI backend first."]
    assert jobs == []


def test_new_session_online_runs_api_call_and_handles_result(window_factory, monkeypatch, fake_api):
    window = window_factory()
    window.online = True
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    window.new_session()
    assert len(jobs) == 1
    worker, done = jobs[0]
    fake_api.create_session.return_value = {
        "session_id": "new-session", "state": "CREATED"
    }
    result = worker()
    assert result["session_id"] == "new-session"
    fake_api.create_session.assert_called_once_with(window.active_vehicle.to_json())
    done(result)
    assert window.session.session_id == "new-session"
    assert window.session.state == "CREATED"


def test_refresh_telemetry_updates_current_session_and_ignores_stale_result(
    window_factory, monkeypatch, fake_api
):
    window = window_factory()
    window.session = Session("session-current", "ACQUIRING", window.active_vehicle)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    fake_api.telemetry_summary.return_value = {"signals": [{"pid": "RPM"}]}
    fake_api.acquisition_records.return_value = {"records": [{"numeric_value": 900}]}

    window.refresh_telemetry()
    assert window._telemetry_refresh_in_flight is True
    window.refresh_telemetry()
    assert len(jobs) == 1  # duplicate polling request is suppressed
    worker, done = jobs[0]
    result = worker()
    done(result)
    assert window._telemetry_refresh_in_flight is False
    assert window.telemetry == {"signals": [{"pid": "RPM"}]}
    assert window.pages[4]._records_data == [{"numeric_value": 900}]

    # A late result from an old session must not overwrite the current session.
    window.session = Session("session-old", "ACQUIRING", window.active_vehicle)
    jobs.clear()
    window.refresh_telemetry()
    worker, done = jobs[0]
    result = worker()
    window.session = Session("session-new", "ACQUIRING", window.active_vehicle)
    previous_telemetry = dict(window.telemetry)
    done(result)
    assert window.telemetry == previous_telemetry


def test_refresh_telemetry_reports_api_error_and_releases_in_flight_flag(
    window_factory, monkeypatch, fake_api
):
    window = window_factory()
    window.session = Session("session-error", "ACQUIRING", window.active_vehicle)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    fake_api.telemetry_summary.side_effect = RuntimeError("telemetry unavailable")
    window.refresh_telemetry()
    worker, done = jobs[0]
    done(worker())
    assert window._telemetry_refresh_in_flight is False
    assert window.statusBar().currentMessage() == "Live-data refresh failed: telemetry unavailable"


def test_record_selected_test_posts_result_notes_then_reanalyzes(
    window_factory, monkeypatch, fake_api
):
    window = window_factory()
    window.session = Session("session-test", "READY", window.active_vehicle)
    window.decision = {"candidates": [
        {"id": "candidate-42", "name": "Check LPG pressure", "purpose": "Check delivery",
         "priority_score": 0.9, "risk": "LOW"}
    ]}
    tests_page = TestsPO(window)
    tests_page.refresh()
    tests_page.select()
    tests_page.set_result("FAIL")
    tests_page.set_notes("Pressure below spec")
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    window.record_selected_test()
    assert len(jobs) == 1
    worker, done = jobs[0]
    fake_api.record_test_result.return_value = {"ok": True}
    fake_api.analyze.return_value = {"state": "ANALYZED"}
    fake_api.decision_plan.return_value = {"candidates": []}
    result = worker()
    fake_api.record_test_result.assert_called_once_with(
        "session-test", "candidate-42", "FAIL",
        notes="Pressure below spec", language="en"
    )
    fake_api.analyze.assert_called_once_with("session-test", language="en")
    fake_api.decision_plan.assert_called_once_with("session-test")
    assert result == {"candidates": []}
    assert callable(done)


def test_record_selected_test_requires_session_and_selection(window_factory, monkeypatch):
    window = window_factory()
    errors = []
    jobs = []
    monkeypatch.setattr(window, "show_error", errors.append)
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    window.record_selected_test()
    assert errors == ["No active session."]
    assert jobs == []

    window.session = Session("session-test", "READY", window.active_vehicle)
    window.record_selected_test()
    assert errors[-1] == "Select a diagnostic test first."
    assert jobs == []


def test_live_ai_callback_formats_unavailable_provider_result(window_factory):
    window = window_factory()
    window._live_ai_done({
        "ai": {"available": False, "provider": "local", "model": "Qwen",
               "error": "model offline", "text": "No diagnosis produced."},
        "telemetry": {"signals": []},
        "session": {"state": "ANALYSIS_READY"},
    })
    text = window.pages[4].ai_box.toPlainText()
    assert "Provider: local" in text
    assert "Model: Qwen" in text
    assert "No diagnosis produced." in text
    assert "Provider error: model offline" in text
    assert window.telemetry == {"signals": []}


def test_device_action_callback_replaces_device_and_updates_status(window_factory):
    window = window_factory()
    window.devices = [{"device_id": "dev-1", "status": "disconnected"}]
    result = {"device_id": "dev-1", "status": "connected"}
    window._device_action_done(result, "Device connected")
    assert window.devices == [result]
    assert window.statusBar().currentMessage() == "Device connected"
