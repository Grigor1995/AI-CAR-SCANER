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


class ResultsPageObject:
    def __init__(self, window):
        self.window = window
        self.page = window.pages[6]

    def refresh(self):
        self.page.refresh()
        if self.page.list.count() and self.page.list.currentRow() < 0:
            self.page.list.setCurrentRow(0)

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
    # Loading a saved vehicle does not implicitly select it as active.
    window.active_vehicle = window.vehicles[0]
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
    page = ResultsPageObject(window)
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
    tests_page = ResultsPageObject(window)
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



# ------------------------- Additional branch coverage -------------------------

def test_translation_helpers_preserve_non_string_values_and_unknown_language():
    assert ui._translate_ui_text(None, "hy") is None
    assert ui._translate_ui_block(123, "ru") == 123
    assert ui._translate_ui_text("Dashboard", "fr") == "Dashboard"


def test_vehicle_dialog_falls_back_when_offline_catalog_is_unreadable(qapp, monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "_resource_path", lambda _name: tmp_path / "catalog-missing.json")
    parent = QWidget()
    parent.language = "hy"
    parent.api = type("OfflineApi", (), {"vehicle_catalog_entries": lambda self: []})()
    dialog = ui.VehicleDialog(parent)
    assert dialog.make.currentText() == "Mercedes-Benz"
    assert dialog.model.currentText() == "E-Class"
    assert dialog.chassis.currentText() == "W211"
    assert "Օֆլայն կատալոգ" in dialog.findChildren(ui.QLabel)[0].text()
    dialog.close()


def test_vehicle_dialog_ignores_invalid_offline_rows_and_non_list_payload(qapp, monkeypatch, tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text('{"vehicles": {"not": "a list"}}', encoding="utf-8")
    monkeypatch.setattr(ui, "_resource_path", lambda _name: catalog)
    parent = QWidget()
    parent.api = type("SparseApi", (), {
        "vehicle_catalog_entries": lambda self: [
            None, {"make": "Kia", "model": "Forte"}
        ]
    })()
    dialog = ui.VehicleDialog(parent)
    assert dialog.make.currentText() == "Mercedes-Benz"
    assert dialog.vehicle().engine == "M272 E35 3.5"
    dialog.close()


def test_settings_dialog_saves_language_and_theme(window_factory, monkeypatch):
    window = window_factory()
    def accept_with_new_values(dialog):
        combos = dialog.findChildren(ui.QComboBox)
        language = next(c for c in combos if c.findData("ru") >= 0)
        theme = next(c for c in combos if c.findData(False) >= 0)
        language.setCurrentIndex(language.findData("ru"))
        theme.setCurrentIndex(theme.findData(False))
        return ui.QDialog.Accepted
    monkeypatch.setattr(ui.QDialog, "exec", accept_with_new_values)
    window._open_settings()
    assert window.language == "ru"
    assert window.dark_theme is False
    assert window.settings_store.value("language") == "ru"
    assert window.settings_store.value("dark_theme") is False
    assert window.statusBar().currentMessage().startswith("Настройки сохранены")


def test_settings_dialog_cancel_does_not_change_preferences(window_factory, monkeypatch):
    window = window_factory()
    monkeypatch.setattr(ui.QDialog, "exec", lambda _dialog: ui.QDialog.Rejected)
    window._open_settings()
    assert window.language == "en"
    assert window.dark_theme is True
    assert window.settings_store.value("language") == "en"


def test_add_vehicle_cancel_does_not_persist_or_start_session(window_factory, monkeypatch):
    window = window_factory()
    before = list(window.vehicles)
    class CancelDialog:
        def __init__(self, _parent):
            pass
        def exec(self):
            return ui.QDialog.Rejected
    monkeypatch.setattr(ui, "VehicleDialog", CancelDialog)
    window.add_vehicle()
    assert window.vehicles == before
    assert window._test_store.saved == []


def test_add_vehicle_replaces_duplicate_profile_and_starts_new_session(window_factory, monkeypatch, vehicle):
    window = window_factory()
    new_vehicle = Vehicle(vehicle.make, vehicle.model, vehicle.chassis, vehicle.year, "M272 upgraded", ["LPG"], vehicle.ecu)
    class AcceptedDialog:
        def __init__(self, _parent):
            pass
        def exec(self):
            return ui.QDialog.Accepted
        def vehicle(self):
            return new_vehicle
    monkeypatch.setattr(ui, "VehicleDialog", AcceptedDialog)
    start = Mock()
    monkeypatch.setattr(window, "new_session", start)
    window.add_vehicle()
    assert window.vehicles == [new_vehicle]
    assert window.active_vehicle is new_vehicle
    assert window._test_store.saved[-1] == [new_vehicle]
    start.assert_called_once()


def test_delete_vehicle_reports_missing_selection_and_stale_index(window_factory, monkeypatch):
    window = window_factory()
    errors = []
    monkeypatch.setattr(window, "show_error", errors.append)
    window.delete_selected_vehicle()
    assert errors == ["Select a vehicle to delete."]

    page = window.pages[1]
    page.refresh()
    page.list.setCurrentRow(0)
    window.vehicles.clear()
    window.delete_selected_vehicle()
    assert errors[-1] == "Selected vehicle is no longer available."


def test_delete_vehicle_respects_cancel_confirmation(window_factory, monkeypatch):
    window = window_factory()
    window.pages[1].refresh()
    window.pages[1].list.setCurrentRow(0)
    monkeypatch.setattr(ui.QMessageBox, "question", lambda *_args, **_kwargs: ui.QMessageBox.No)
    original = list(window.vehicles)
    window.delete_selected_vehicle()
    assert window.vehicles == original
    assert window._test_store.saved == []


def test_delete_vehicle_removes_confirmed_profile_and_clears_active_vehicle(window_factory, monkeypatch):
    window = window_factory()
    window.pages[1].refresh()
    window.pages[1].list.setCurrentRow(0)
    monkeypatch.setattr(ui.QMessageBox, "question", lambda *_args, **_kwargs: ui.QMessageBox.Yes)
    window.delete_selected_vehicle()
    assert window.vehicles == []
    assert window.active_vehicle is None
    assert window._test_store.saved[-1] == []
    assert window.statusBar().currentMessage().startswith("Vehicle deleted:")


def test_refresh_health_success_and_offline_callbacks(window_factory, monkeypatch, fake_api):
    window = window_factory()
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    monkeypatch.setattr(window, "refresh_pages", Mock())
    fake_api.health.return_value = {"status": "ok"}
    window.refresh_health()
    work, done = jobs.pop()
    done(work())
    assert window.online is True
    assert window.statusBar().currentMessage() == "Backend online"

    fake_api.health.return_value = {"status": "starting"}
    window.refresh_health()
    work, done = jobs.pop()
    done(work())
    assert window.online is False
    assert window.statusBar().currentMessage() == "Backend offline"


def test_refresh_pages_isolates_a_page_refresh_failure(window_factory, monkeypatch):
    window = window_factory()
    monkeypatch.setattr(window.pages[2], "refresh", Mock(side_effect=RuntimeError("broken page")))
    language = Mock()
    monkeypatch.setattr(window, "_apply_language", language)
    window.refresh_pages()
    language.assert_called_once()


def test_scan_devices_and_device_added_callbacks(window_factory, monkeypatch, fake_api):
    window = window_factory()
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    fake_api.scan_devices.return_value = {"devices": [{"device_id": "usb-1"}]}
    window.scan_devices("usb")
    work, done = jobs.pop(0)
    done(work())
    assert window.devices == [{"device_id": "usb-1"}]
    assert window.statusBar().currentMessage() == "VCI devices: 1"

    jobs.clear()
    fake_api.add_simulator_device.return_value = {"device_id": "sim-1"}
    fake_api.list_devices.return_value = {"devices": [{"device_id": "sim-1"}]}
    window.add_simulator_device()
    work, done = jobs.pop(0)
    done(work())
    assert window.selected_device_id == "sim-1"
    assert len(jobs) == 1
    refresh_work, refresh_done = jobs.pop(0)
    refresh_done(refresh_work())
    assert window.devices == [{"device_id": "sim-1"}]


def test_probe_wifi_rejects_blank_host_and_runs_with_trimmed_host(window_factory, monkeypatch, fake_api):
    window = window_factory()
    errors = []
    jobs = []
    monkeypatch.setattr(window, "show_error", errors.append)
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    window.probe_wifi()
    assert errors == ["Enter the Wi-Fi OBD adapter host, for example 192.168.0.10."]
    assert jobs == []

    page = window.pages[2]
    page.host.setText(" 192.0.2.44 ")
    page.port.setValue(35001)
    fake_api.probe_wifi.return_value = {"device_id": "wifi-1"}
    window.probe_wifi()
    work, done = jobs.pop(0)
    assert work() == {"device_id": "wifi-1"}
    fake_api.probe_wifi.assert_called_once_with("192.0.2.44", 35001)
    done({"device_id": "wifi-1"})
    assert window.selected_device_id == "wifi-1"


@pytest.mark.parametrize(
    ("action_name", "api_name", "result", "message"),
    [
        ("connect_selected_device", "connect_device", {"device_id": "dev-1", "status": "connected"}, "Device connected"),
        ("disconnect_selected_device", "disconnect_device", {"device_id": "dev-1", "status": "disconnected"}, "Device disconnected"),
        ("reconnect_selected_device", "reconnect_device", {"device_id": "dev-1", "status": "connected"}, "Device reconnected"),
    ],
)
def test_device_connection_actions_dispatch_and_refresh(window_factory, monkeypatch, fake_api, action_name, api_name, result, message):
    window = window_factory()
    window.devices = [{"device_id": "dev-1", "status": "disconnected", "connection_type": "USB", "metadata": {}}]
    window.selected_device_id = "dev-1"
    window.pages[2].refresh()
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    getattr(fake_api, api_name).return_value = result
    getattr(window, action_name)()
    assert len(jobs) == 1
    work, done = jobs.pop(0)
    assert work() == result
    done(result)
    assert window.devices == [result]
    assert window.statusBar().currentMessage() == message


@pytest.mark.parametrize(
    ("action_name", "api_name", "payload", "expected"),
    [
        ("read_device_vin", "device_vin", {"vin": "WDD2110801A123456"}, "VIN: WDD2110801A123456"),
        ("read_device_dtcs", "device_dtcs", {"dtcs": ["P0102", "P0302"]}, "DTCs:\nP0102\nP0302"),
        ("read_device_dtcs", "device_dtcs", {"dtcs": []}, "No stored generic OBD-II DTCs"),
        ("read_device_live_data", "device_live_data", {"values": {"rpm": 900}}, "{'rpm': 900}"),
    ],
)
def test_device_read_callbacks_render_results(window_factory, monkeypatch, fake_api, action_name, api_name, payload, expected):
    window = window_factory()
    window.devices = [{"device_id": "dev-1", "status": "connected", "connection_type": "USB", "metadata": {}}]
    window.selected_device_id = "dev-1"
    window.pages[2].refresh()
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    getattr(fake_api, api_name).return_value = payload
    getattr(window, action_name)()
    work, done = jobs.pop()
    done(work())
    assert expected in window.pages[2].result.toPlainText()


def test_session_created_resets_analysis_state_and_opens_diagnostic_page(window_factory, monkeypatch):
    window = window_factory()
    window.telemetry = {"old": True}
    window.network = {"ecus": [{"id": "old"}]}
    window.active_network = {"old": True}
    refresh = Mock()
    monkeypatch.setattr(window, "refresh_pages", refresh)
    window._session_created({"session_id": "s-new", "state": "CREATED", "evidence": []})
    assert window.session.session_id == "s-new"
    assert window.session_json["evidence"] == []
    assert window.decision == {}
    assert window.telemetry == {}
    assert window.network == {}
    assert window.active_network == {}
    assert window.nav.currentRow() == 3
    refresh.assert_called_once()
    assert window.statusBar().currentMessage() == "Diagnostic session created"


def test_analyze_input_supports_dtc_only_and_decision_callback(window_factory, monkeypatch, fake_api):
    window = window_factory()
    window.session = Session("s-dtc", "READY", window.active_vehicle)
    window.pages[3].dtc.setText("P0302")
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    fake_api.analyze.return_value = {"session_id": "s-dtc", "state": "ANALYZED"}
    window.analyze_input()
    work, done = jobs.pop()
    done(work())
    fake_api.add_dtc.assert_called_once_with("s-dtc", "P0302")
    fake_api.ingest_evidence.assert_not_called()
    assert window.session.state == "ANALYZED"
    decision_work, decision_done = jobs.pop()
    fake_api.decision_plan.return_value = {"candidates": []}
    decision_done(decision_work())
    assert window.decision == {"candidates": []}
    assert window.statusBar().currentMessage() == "Diagnostic reasoning updated"


def test_new_session_without_profiles_opens_vehicle_dialog(window_factory, monkeypatch):
    window = window_factory(vehicles=[])
    add = Mock()
    monkeypatch.setattr(window, "add_vehicle", add)
    window.new_session()
    add.assert_called_once()


def test_simulator_and_telemetry_actions_are_guarded_by_session(window_factory, monkeypatch, fake_api):
    window = window_factory()
    jobs = []
    errors = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    monkeypatch.setattr(window, "show_error", errors.append)

    window.start_simulator()
    assert errors == ["Backend is offline. Start the FastAPI backend first."]
    assert jobs == []
    window.stop_simulator()
    window.analyze_telemetry()
    window.refresh_network()
    window.active_probe()
    assert jobs == []

    window.session = Session("s-live", "READY", window.active_vehicle)
    fake_api.start_simulator.return_value = {"state": "RUNNING"}
    window.start_simulator()
    work, done = jobs.pop()
    assert work() == {"state": "RUNNING"}
    callback = Mock()
    monkeypatch.setattr(window, "_sim_changed", callback)
    done({"state": "RUNNING"})
    callback.assert_called_once_with("Simulator acquisition started")

    fake_api.stop_acquisition.return_value = {"state": "STOPPED"}
    window.stop_simulator()
    work, done = jobs.pop()
    done(work())
    callback.assert_called_with("Acquisition stopped")

    fake_api.analyze_telemetry.return_value = {"signals": []}
    window.analyze_telemetry()
    work, done = jobs.pop()
    done(work())
    assert window.telemetry == {"signals": []}
    assert window.statusBar().currentMessage() == "Telemetry analysis completed"


def test_live_ai_success_and_defaults_update_page(window_factory, monkeypatch):
    window = window_factory()
    errors = []
    monkeypatch.setattr(window, "show_error", errors.append)
    window.ai_analyze_live_data()
    assert errors == ["Create a diagnostic session first."]

    window.session = Session("s-ai", "READY", window.active_vehicle)
    window._live_ai_done({"ai": {"available": True, "provider": "cloud", "model": "model-x", "text": "Evidence-based summary"}})
    text = window.pages[4].ai_box.toPlainText()
    assert "Provider: cloud | Model: model-x | Available: True" in text
    assert "Evidence-based summary" in text
    assert "Provider error:" not in text
    assert window.statusBar().currentMessage() == "Live-data AI analysis completed"


@pytest.mark.parametrize(
    ("network", "expected_ids"),
    [
        ({"ecus": [{"id": "ecu-id"}, {"ecu_id": "engine"}, {"name": "skip"}, {"id": 0, "ecu_id": "backup"}]}, ["ecu-id", "engine", "backup"]),
        ({}, None),
    ],
)
def test_active_probe_only_sends_known_ecu_identifiers(window_factory, monkeypatch, fake_api, network, expected_ids):
    window = window_factory()
    window.session = Session("s-net", "READY", window.active_vehicle)
    window.network = network
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    fake_api.active_probe.return_value = {"responding": expected_ids or []}
    window.active_probe()
    work, done = jobs.pop()
    assert work() == {"responding": expected_ids or []}
    fake_api.active_probe.assert_called_once_with("s-net", expected_ids)
    done({"responding": expected_ids or []})
    assert window.active_network == {"responding": expected_ids or []}
    assert window.statusBar().currentMessage() == "Active read-only ECU probe completed"


def test_live_data_request_refresh_gates_and_loads_details(window_factory, monkeypatch, fake_api):
    window = window_factory()
    page = window.pages[4]
    page.request_refresh()
    assert page._details_in_flight is False
    assert fake_api.acquisition_status.call_count == 0

    window.online = True
    window.session = Session("s-live", "READY", window.active_vehicle)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    fake_api.acquisition_status.return_value = {"state": "RUNNING"}
    fake_api.ai_provider_info.return_value = {"available": True, "model": "test-model"}
    fake_api.acquisition_records.return_value = {"records": [{"numeric_value": 720}, {"numeric_value": None}]}
    page.request_refresh()
    assert page._details_in_flight is True
    page.request_refresh()
    assert len(jobs) == 1
    work, done = jobs.pop()
    done(work())
    assert page._details_in_flight is False
    assert page.status.text() == "RUNNING"
    assert page.timer.isActive()
    assert page.ai_status.text().startswith("AI: READY")
    assert page.chart.values == [720.0]
    page.timer.stop()


def test_live_data_request_refresh_handles_provider_and_status_errors(window_factory, monkeypatch, fake_api):
    window = window_factory()
    window.online = True
    window.session = Session("s-live", "READY", window.active_vehicle)
    page = window.pages[4]
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    fake_api.acquisition_status.side_effect = RuntimeError("status timeout")
    fake_api.ai_provider_info.side_effect = RuntimeError("provider timeout")
    fake_api.acquisition_records.return_value = []
    page.request_refresh()
    work, done = jobs.pop()
    done(work())
    assert page.status.text() == "STOPPED"
    assert page.ai_status.text() == "AI: unavailable"
    assert page._records_data == []


def test_live_data_poll_running_refreshes_telemetry_and_stops_when_stopped(window_factory, monkeypatch):
    window = window_factory()
    window.online = True
    window.session = Session("s-live", "READY", window.active_vehicle)
    page = window.pages[4]
    refresh = Mock()
    monkeypatch.setattr(window, "refresh_telemetry", refresh)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    page._poll()
    work, done = jobs.pop()
    done({"state": "RUNNING"})
    refresh.assert_called_once()
    assert page.status.text() == "RUNNING"
    assert page.timer.isActive()
    page._poll_done({"state": "STOPPED"})
    assert page.status.text() == "STOPPED"
    assert not page.timer.isActive()


def test_resource_path_supports_source_and_frozen_layouts(monkeypatch, tmp_path):
    monkeypatch.setattr(ui.sys, "frozen", False, raising=False)
    source_path = ui._resource_path("assets/icon.webp")
    assert source_path.name == "icon.webp"
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    monkeypatch.setattr(ui.sys, "frozen", True, raising=False)
    monkeypatch.setattr(ui.sys, "_MEIPASS", str(bundle), raising=False)
    assert ui._resource_path("assets/icon.webp") == bundle / "assets" / "icon.webp"
