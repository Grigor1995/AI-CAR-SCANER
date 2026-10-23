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

def test_main_window_builds_reference_navigation_pages(window_factory):
    window = window_factory()
    assert window.windowTitle() == "AI Auto Diagnostic Workstation"
    assert window.nav.count() == 11
    assert len(window.pages) == 11
    assert window.stack.count() == 1
    assert window.nav.currentRow() == 0
    assert [window.nav.item(i).text().split()[-1] for i in range(window.nav.count())] == [
        "Dashboard", "Vehicles", "Devices", "Diagnostic", "Data", "Network", "Tests", "DTC", "Analysis", "Reports", "AI"
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
    assert page.session == "READY"
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


def test_record_selected_test_applies_recalculated_session_without_second_analysis(
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
    fake_api.analyze.assert_not_called()
    fake_api.decision_plan.assert_called_once_with("session-test", language="en")
    assert result == {"session": {"ok": True}, "decision": {"candidates": []}}
    done(result)
    assert window.session_json == {"ok": True}
    assert window.decision == {"candidates": []}
    assert window.pages[6].notes.text() == ""


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
    assert any("Օֆլայն կատալոգ" in label.text() for label in dialog.findChildren(ui.QLabel))
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
    new_vehicle = Vehicle(vehicle.make, vehicle.model, vehicle.chassis, vehicle.year, vehicle.engine, ["LPG"], vehicle.ecu)
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
    window.active_vehicle = window.vehicles[0]
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
    assert page.status.text() == "Acquisition unavailable"
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
    page.timer.start()
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


def test_ui_run_starts_without_optional_icon_assets(qapp, monkeypatch, tmp_path):
    class FakeSignal:
        def __init__(self):
            self.callback = None
        def connect(self, callback):
            self.callback = callback

    class FakeApplication:
        def __init__(self):
            self.aboutToQuit = FakeSignal()
            self.setApplicationName = Mock()
            self.setFont = Mock()
            self.setWindowIcon = Mock()
            self.exec = Mock()

    class FakeWindow:
        def __init__(self):
            self._apply_language = Mock()
            self.setWindowIcon = Mock()
            self.setAttribute = Mock()
            self.show = Mock()
            self.windowHandle = Mock(return_value=None)
        def winId(self):
            return 1

    app = FakeApplication()
    window = FakeWindow()
    monkeypatch.setattr(ui.sys, "platform", "linux")
    monkeypatch.setattr(ui, "QApplication", lambda _args: app)
    monkeypatch.setattr(ui, "MainWindow", lambda: window)
    monkeypatch.setattr(ui, "_resource_path", lambda relative: tmp_path / relative)

    ui.run()

    app.setApplicationName.assert_called_once_with("AI Auto Diagnostic Workstation")
    window._apply_language.assert_called_once()
    window.show.assert_called_once()
    window.setWindowIcon.assert_not_called()
    app.exec.assert_called_once()
    assert app.aboutToQuit.callback is not None


def test_ui_run_applies_first_existing_icon_to_app_window_and_handle(qapp, monkeypatch, tmp_path):
    class FakeSignal:
        def connect(self, callback):
            self.callback = callback

    class FakeApplication:
        def __init__(self):
            self.aboutToQuit = FakeSignal()
            self.setApplicationName = Mock()
            self.setFont = Mock()
            self.setWindowIcon = Mock()
            self.exec = Mock()

    class FakeWindow:
        def __init__(self):
            self._apply_language = Mock()
            self.setWindowIcon = Mock()
            self.setAttribute = Mock()
            self.show = Mock()
            self.handle = type("NativeWindow", (), {"setIcon": Mock()})()
            self.windowHandle = Mock(return_value=self.handle)
        def winId(self):
            return 1

    icon_path = tmp_path / "assets" / "AI-Car-Scanner.webp"
    icon_path.parent.mkdir(parents=True)
    icon_path.write_bytes(b"test asset")
    class FakeIcon:
        def __init__(self, path=None):
            self.path = path
        def isNull(self):
            return False

    app = FakeApplication()
    window = FakeWindow()
    monkeypatch.setattr(ui.sys, "platform", "linux")
    monkeypatch.setattr(ui, "QApplication", lambda _args: app)
    monkeypatch.setattr(ui, "MainWindow", lambda: window)
    monkeypatch.setattr(ui, "QIcon", FakeIcon)
    monkeypatch.setattr(ui, "_resource_path", lambda relative: tmp_path / relative)

    ui.run()

    assert app.setWindowIcon.call_count == 1
    assert app.setWindowIcon.call_args.args[0].path == str(icon_path)
    assert window.setWindowIcon.call_count == 2
    window.handle.setIcon.assert_called_once()
    app.exec.assert_called_once()


def test_windows_taskbar_icon_returns_early_for_null_icon(qapp, monkeypatch):
    monkeypatch.setattr(ui.sys, "platform", "win32")
    ui._set_windows_taskbar_icon(123, ui.QIcon())

def test_vehicle_dialog_handles_api_failure_and_malformed_offline_catalog(qapp, monkeypatch, tmp_path):
    parent = QWidget()
    parent.language = "ru"
    parent.api = Mock()
    parent.api.vehicle_catalog_entries.side_effect = RuntimeError("catalog service offline")
    malformed = tmp_path / "catalog.json"
    malformed.write_text('{"vehicles": "not-a-list"}', encoding="utf-8")
    monkeypatch.setattr(ui, "_resource_path", lambda _relative: malformed)

    dialog = ui.VehicleDialog(parent)
    assert dialog._catalog_from_server is False
    assert dialog._catalog == []
    # When both server and offline catalogs are unavailable, the dialog keeps
    # its curated W211 defaults instead of leaving vehicle selection unusable.
    assert dialog.make.count() == 1
    assert dialog.make.currentText() == "Mercedes-Benz"
    assert dialog.model.currentText() == "E-Class"
    assert dialog.chassis.currentText() == "W211"
    assert any("Офлайн-каталог" in label.text() for label in dialog.findChildren(ui.QLabel))
    dialog.close()


def test_refresh_telemetry_handles_error_stale_session_and_success(window_factory, monkeypatch):
    window = window_factory()
    window.session = Session("session-before-refresh", "READY", window.active_vehicle)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    refresh_pages = Mock()
    monkeypatch.setattr(window, "refresh_pages", refresh_pages)

    # Backend exception is returned through the worker, not raised on the UI thread.
    window.api.telemetry_summary.side_effect = RuntimeError("summary unavailable")
    window.refresh_telemetry()
    work, done = jobs.pop()
    assert work() == {"_error": "summary unavailable"}
    done({"_error": "summary unavailable"})
    assert "Live-data refresh failed" in window.statusBar().currentMessage()
    assert window._telemetry_refresh_in_flight is False

    # A successful response for an obsolete session must not overwrite current UI state.
    window.api.telemetry_summary.side_effect = None
    window.api.telemetry_summary.return_value = {"sample_count": 4}
    window.api.acquisition_records.return_value = {"records": [{"numeric_value": 750}]}
    window.refresh_telemetry()
    _work, stale_done = jobs.pop()
    window.session = Session("new-session", "READY", window.active_vehicle)
    stale_done({"summary": {"sample_count": 4}, "records": {"records": [{"numeric_value": 750}]}})
    assert window.telemetry == {}
    refresh_pages.assert_not_called()

    # The response applies when the session id still matches.
    window.refresh_telemetry()
    work, done = jobs.pop()
    payload = work()
    assert payload["summary"] == {"sample_count": 4}
    done(payload)
    assert window.telemetry == {"sample_count": 4}
    assert window.pages[4]._records_data == [{"numeric_value": 750}]
    refresh_pages.assert_called_once()


def test_live_ai_analysis_guards_missing_session_and_renders_fallback_or_success(window_factory, monkeypatch):
    window = window_factory()
    errors = []
    jobs = []
    monkeypatch.setattr(window, "show_error", errors.append)
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))

    window.ai_analyze_live_data()
    assert errors == ["Create a diagnostic session first."]
    assert jobs == []

    window.session = Session("session-ai", "READY", window.active_vehicle)
    window.api.ai_analyze_live_data.return_value = {"ai": {"available": True, "provider": "local", "model": "qwen", "text": "Evidence-based result"}}
    window.ai_analyze_live_data()
    work, done = jobs.pop()
    assert work() == window.api.ai_analyze_live_data.return_value

    refresh_pages = Mock()
    monkeypatch.setattr(window, "refresh_pages", refresh_pages)
    done({
        "ai": {"available": False, "provider": "fallback", "model": "offline", "text": "Deterministic result", "error": "server offline"},
        "telemetry": {"sample_count": 1},
        "session": {"state": "ANALYZED"},
    })
    displayed = window.pages[4].ai_box.toPlainText()
    assert "Provider: fallback" in displayed
    assert "Provider error: server offline" in displayed
    assert window.telemetry == {"sample_count": 1}
    assert window.session_json == {"state": "ANALYZED"}
    refresh_pages.assert_called_once()



def test_close_waits_for_active_api_workers_before_destroying_qthreads(window_factory):
    """Closing a window must not destroy a still-running native QThread."""
    window = window_factory()
    active_worker = Mock()
    window._workers.append(active_worker)

    window.close()

    assert window._closing is True
    assert window.isVisible() is True
    assert window.isEnabled() is False
    active_worker.requestInterruption.assert_called_once()

    # Mimic delivery of the QThread.finished signal once the HTTP call ends.
    # The QObject receiver handles actual finished-signal bookkeeping.
    window._workers.clear()
    window.close()
    assert window.isVisible() is False


def test_run_worker_rejects_new_background_jobs_after_shutdown_requested(window_factory):
    window = window_factory()
    window._closing = True
    window.run_worker(lambda: object(), lambda _result: None)
    assert window._workers == []



def test_shutdown_trace_is_opt_in_and_records_event_loop_stages(monkeypatch, tmp_path):
    trace_path = tmp_path / "qt-shutdown.log"
    monkeypatch.delenv("AI_CAR_SHUTDOWN_TRACE_PATH", raising=False)
    ui._trace_shutdown("before")
    assert not trace_path.exists()

    monkeypatch.setenv("AI_CAR_SHUTDOWN_TRACE_PATH", str(trace_path))
    ui._trace_shutdown("ui: QApplication.exec returned rc=0")
    ui._trace_shutdown("ui: returning to main.run")
    assert trace_path.read_text(encoding="utf-8").splitlines() == [
        "ui: QApplication.exec returned rc=0",
        "ui: returning to main.run",
    ]



def test_shutdown_trace_ignores_unwritable_report_directory(monkeypatch, tmp_path):
    """A failed diagnostics log write must not break GUI teardown."""
    monkeypatch.setenv(
        "AI_CAR_SHUTDOWN_TRACE_PATH", str(tmp_path / "missing-dir" / "shutdown.log")
    )
    ui._trace_shutdown("closing with missing parent directory")
    assert not (tmp_path / "missing-dir").exists()


def test_worker_finished_waits_then_releases_strong_reference(window_factory, monkeypatch):
    """A finished QThread must be joined before destroying its wrapper."""
    window = window_factory()
    worker = Mock()
    window._workers.append(worker)
    monkeypatch.setattr(ui.MainWindow, "sender", lambda self: worker)

    window._on_worker_finished()

    worker.wait.assert_called_once_with()
    worker.deleteLater.assert_called_once_with()
    assert worker not in window._workers


def test_demo_dashboard_quick_actions_open_real_diagnostic_pages(window_factory):
    window = window_factory()
    dashboard = window.pages[0]
    button = next(b for b in dashboard.findChildren(QPushButton) if 'DTC list' in b.text())
    button.click()
    assert window.nav.currentRow() == 7
    window.session_json = {'dtcs': [{'code': 'P0302', 'description': 'Cylinder 2', 'source': 'USER_REPORTED'}]}
    window.pages[7].refresh()
    assert 'P0302' in window.pages[7].list.item(0).text()
    assert 'USER_REPORTED' in window.pages[7].list.item(0).text()


def test_demo_signals_never_mix_independent_channels(window_factory):
    window = window_factory()
    grid = window.pages[0].signals
    grid.set_records([
        {'pid': 'RPM', 'numeric_value': 800, 'unit': 'rpm'},
        {'pid': 'coolant', 'numeric_value': 88, 'unit': 'C'},
        {'pid': 'RPM', 'numeric_value': 900, 'unit': 'rpm'},
    ])
    assert grid.cards[0].trace.values == [800, 900]
    assert grid.cards[1].trace.values == [88]
    assert grid.cards[2].trace.values == []


def test_report_export_escapes_session_content(window_factory, monkeypatch, tmp_path):
    from apps.desktop import demo_ui
    window = window_factory()
    window.session_json = {'session_id': 'test', 'symptom': '<script>unsafe</script>'}
    destination = tmp_path / 'report.html'
    monkeypatch.setattr(demo_ui.QFileDialog, 'getSaveFileName', lambda *a: (str(destination), 'HTML'))
    window.pages[9].export()
    contents = destination.read_text()
    assert '&lt;script&gt;' in contents
    assert '<script>' not in contents


@pytest.mark.parametrize("pixel_font", [False, True])
def test_native_pdf_export_hides_session_id_and_preserves_diagnostic_content(window_factory, monkeypatch, tmp_path, pixel_font):
    from apps.desktop import demo_ui
    from pypdf import PdfReader
    window = window_factory()
    if pixel_font:
        from PySide6.QtGui import QFont
        class PixelFontDocument(demo_ui.QTextDocument):
            def __init__(self):
                super().__init__()
                font = QFont()
                font.setPixelSize(16)
                self.setDefaultFont(font)
        monkeypatch.setattr(demo_ui, 'QTextDocument', PixelFontDocument)
    window.session_json = {'session_id': 'pdf-session-123', 'dtcs': [{'code': 'P0302'}]}
    destination = tmp_path / 'report.pdf'
    monkeypatch.setattr(demo_ui.QFileDialog, 'getSaveFileName', lambda *a: (str(destination), 'PDF'))
    window.pages[9].export()
    assert destination.read_bytes().startswith(b'%PDF')
    text = ''.join(page.extract_text() for page in PdfReader(destination).pages)
    assert 'pdf-session-123' not in text
    assert 'session_id' not in text
    assert 'P0302' in text


def test_history_open_clears_previous_vehicle_telemetry(window_factory):
    window = window_factory()
    window.telemetry = {'signals': [{'pid': 'RPM', 'mean': 2000}]}
    window.pages[4]._records_data = [{'channel': 'RPM', 'numeric_value': 2000}]
    window.network = {'ecus': [{'ecu_id': 'old'}]}
    window.pages[9].opened({'session_id': 'reopened-session', 'state': 'CREATED', 'recommendations': []})
    assert window.session.session_id == 'reopened-session'
    assert window.pages[4]._records_data == []
    assert window.telemetry == {}
    assert window.network == {}
    assert window.nav.currentRow() == 8


def test_live_details_from_previous_session_cannot_overwrite_current_session(window_factory, monkeypatch):
    window = window_factory()
    window.online = True
    window.session = Session('old-session')
    callbacks = []
    monkeypatch.setattr(window, 'run_worker', lambda fn, done: callbacks.append(done))
    live = window.pages[4]
    live.request_refresh()
    window.session = Session('new-session')
    callbacks[0]({'records': {'records': [{'channel': 'RPM', 'numeric_value': 2000}]}})
    assert live._records_data == []
    assert live._details_in_flight is False


def test_refresh_preserves_vehicle_selection_and_cached_artwork(window_factory, vehicle, monkeypatch):
    other = Vehicle("BMW", "3 Series", "E90", 2010, "N52", ["Petrol"], "MSV70")
    window = window_factory([vehicle, other])
    page = window.pages[1]
    page.refresh()
    page.list.setCurrentRow(1)
    render = Mock(wraps=ui.vehicle_pixmap)
    monkeypatch.setattr(ui, "vehicle_pixmap", render)
    page.refresh()
    assert page.list.currentRow() == 1
    assert page.edit_btn.isEnabled()
    assert "BMW" in page.details.toPlainText()
    render.assert_not_called()


def test_edit_dialog_keeps_custom_vehicle_and_uses_cached_catalog(window_factory, fake_api):
    window = window_factory()
    custom = Vehicle("Custom", "Model X", "CX", 2020, "Engine", ["Diesel"], "ECU-X")
    dialog = ui.VehicleDialog(window)
    dialog.set_vehicle(custom)
    assert dialog.vehicle() == custom
    fake_api.vehicle_catalog_entries.assert_not_called()
    dialog.deleteLater()


def test_edit_saved_vehicle_persists_replacement(window_factory, monkeypatch, vehicle):
    window = window_factory()
    page = window.pages[1]
    page.refresh()
    replacement = Vehicle("BMW", "3 Series", "E90", 2010, "N52", ["Petrol"], "MSV70")
    class Dialog:
        def __init__(self, parent): pass
        def set_vehicle(self, selected): assert selected == vehicle
        def exec(self): return ui.QDialog.Accepted
        def vehicle(self): return replacement
        def deleteLater(self): pass
    monkeypatch.setattr(ui, "VehicleDialog", Dialog)
    window.edit_selected_vehicle()
    assert window.vehicles == [replacement]
    assert window._test_store.load() == [replacement]


def test_language_refresh_requests_localized_data_and_discards_stale_response(window_factory, monkeypatch, fake_api):
    window = window_factory()
    window.online = True
    window.session = Session("s-1", "READY", window.active_vehicle)
    window.language = "hy"
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda fn, done: jobs.append((fn, done)))
    window._refresh_response_language()
    worker, done = jobs[0]
    fake_api.get_session.return_value = {"state": "READY"}
    fake_api.decision_plan.return_value = {"candidates": []}
    result = worker()
    fake_api.get_session.assert_called_once_with("s-1", language="hy")
    fake_api.decision_plan.assert_called_once_with("s-1", language="hy")
    window.language = "ru"
    done(result)
    assert window.session_json == {}


def test_empty_current_plan_does_not_count_historical_results(window_factory):
    window = window_factory()
    window.session_json = {"test_results": [
        {"test_id": "finished", "result": "PASS"},
        {"test_id": "reopened", "result": "PASS"},
        {"test_id": "reopened", "result": "INCOMPLETE"},
    ]}
    window.decision = {"candidates": []}
    window.pages[6].refresh()
    assert window.pages[6].progress.value() == 0
    assert window.pages[6].progress.format() == "0/0"
    window.pages[0].refresh()
    assert window.pages[0].progress.value() == 0


@pytest.mark.parametrize("language", ["hy", "ru"])
def test_dashboard_labels_and_dynamic_lists_translate_after_refresh(window_factory, language):
    window = window_factory()
    window.language = language
    window.session_json = {"dtcs": [{"code": "P0302"}], "hypotheses": []}
    window.refresh_pages()
    labels = [item.text() for item in window.findChildren(ui.QLabel)]
    assert "No acquisition samples" not in labels
    assert "No recommended tests yet" not in labels
    assert "No acquisition running" not in labels
    dtc = window.pages[7].list.item(0).text()
    assert "P0302" in dtc
    assert "No description supplied" not in dtc
    assert "Source:" not in dtc
    assert "Add evidence and analyze the session to generate hypotheses" not in window.pages[8].list.item(0).text()
    window.language = "en"
    window._apply_language()
    assert "No description supplied" in window.pages[7].list.item(0).text()


def test_dashboard_presentation_strings_have_hy_and_ru_translations():
    import ast
    import re
    from pathlib import Path
    tree = ast.parse(Path(ui.__file__).with_name("demo_ui.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        argument = node.args[0]
        function = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
        if function not in {"label", "action", "Panel", "CountCard", "setPlaceholderText", "setText"}:
            continue
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str) and re.search("[a-zA-Z]", argument.value):
            for language in ("hy", "ru"):
                translated = ui._translate_ui_text(argument.value, language)
                assert translated != argument.value, (language, argument.value)


def test_async_status_messages_use_selected_language_immediately(window_factory, monkeypatch):
    window=window_factory()
    window.language="hy"
    monkeypatch.setattr(window,"refresh_pages",lambda:None)
    window._decision_done({"candidates":[]})
    assert window.statusBar().currentMessage()==window.tr_text("Diagnostic reasoning updated")
    assert window.statusBar().currentMessage()!="Diagnostic reasoning updated"


def test_history_language_switch_rebuilds_labels_without_network_or_losing_selection(window_factory):
    window=window_factory()
    page=window.pages[9]
    page.loaded([{"session_id":"history-1","state":"TESTING","vehicle":{"make":"BMW","model":"3 Series"},"test_results":[]}])
    page.history.setCurrentRow(0)
    window.language="hy"
    page.refresh()
    assert "TESTING" not in page.history.item(0).text()
    assert "results" not in page.history.item(0).text()
    assert "BMW" in page.history.item(0).text()
    assert page.history.currentItem().data(Qt.UserRole)=="history-1"


def test_session_id_stays_internal_in_dashboard_diagnostics_and_history(window_factory):
    window = window_factory()
    secret = "private-session-abcdef"
    window.session = Session(secret, "TESTING", window.active_vehicle)
    window.pages[0].refresh()
    window.pages[3].refresh()
    window.pages[9].loaded([{"session_id": secret, "state": "TESTING", "dtcs": [], "test_results": []}])
    assert secret not in window.pages[0].session.value.text()
    assert secret not in window.pages[3].lbl.text()
    item = window.pages[9].history.item(0)
    assert secret not in item.text()
    assert item.data(Qt.UserRole) == secret
    assert window.session.session_id == secret
def test_backend_health_autoreconnect_is_non_modal(window_factory, monkeypatch, fake_api):
    window = window_factory()
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    monkeypatch.setattr(window, "refresh_pages", Mock())
    assert window._health_timer.interval() == 12000

    fake_api.health.side_effect = ConnectionError("temporary backend outage")
    window.refresh_health()
    work, done = jobs.pop()
    assert work()["status"] == "offline"
    done(work())
    assert window.online is False
    assert window.statusBar().currentMessage() == "Backend offline"
    assert window._health_pending is False

    fake_api.health.side_effect = None
    fake_api.health.return_value = {"status": "ok"}
    window.refresh_health()
    work, done = jobs.pop()
    done(work())
    assert window.online is True
    assert window.statusBar().currentMessage() == "Backend online"

    fake_api.health.return_value = {"status": "not_ok"}
    window.refresh_health()
    work, done = jobs.pop()
    done(work())
    assert window.online is False

    fake_api.health.return_value = {"status": "ok"}
    window.refresh_health()
    work, done = jobs.pop()
    done(work())
    assert window.statusBar().currentMessage() == "Backend recovered"




def test_fastapi_health_timer_reconnects_without_modal_failures(
    window_factory, monkeypatch, fake_api,
):
    window = window_factory()
    assert window._health_timer.isActive()
    assert window._health_timer.interval() == 12000
    pending = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: pending.append((work, done)))
    monkeypatch.setattr(window, "refresh_pages", Mock())

    fake_api.health.side_effect = ConnectionError("temporary service restart")
    window.refresh_health()
    window.refresh_health()  # never submit overlapping health checks
    assert len(pending) == 1
    work, done = pending.pop()
    assert work() == {"status": "offline"}
    done(work())
    assert window.online is False
    assert window._health_pending is False
    assert window.statusBar().currentMessage() == "Backend offline"

    fake_api.health.side_effect = None
    fake_api.health.return_value = {"status": "ok"}
    window.refresh_health()
    work, done = pending.pop()
    done(work())
    assert window.online is True
    assert window.statusBar().currentMessage() == "Backend online"

    fake_api.health.return_value = {"status": "starting"}
    window.refresh_health()
    work, done = pending.pop()
    done(work())
    assert window.online is False

    fake_api.health.return_value = {"status": "ok"}
    window.refresh_health()
    work, done = pending.pop()
    done(work())
    assert window.online is True
    assert window.statusBar().currentMessage() == "Backend recovered"

    window.close()
    assert not window._health_timer.isActive()


def test_backend_recovery_refreshes_provider_on_actual_live_data_navigation(window_factory, monkeypatch, fake_api):
    window = window_factory()
    window.session = Session("private-session", "TESTING", window.active_vehicle)
    window.nav.setCurrentRow(4)
    assert window.stack.currentIndex() == 0
    monkeypatch.setattr(window, "refresh_pages", Mock())
    request_refresh = Mock()
    monkeypatch.setattr(window.pages[4], "request_refresh", request_refresh)
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    fake_api.health.return_value = {"status": "ok"}
    window.refresh_health()
    work, done = jobs.pop()
    done(work())
    request_refresh.assert_called_once()


def test_connected_adapter_button_dispatches_backend_acquisition(window_factory, monkeypatch, fake_api):
    window = window_factory()
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append((work, done)))
    window.start_bound_acquisition()
    assert jobs == []
    window.session = Session("s-bound", "READY", window.active_vehicle)
    fake_api.start_bound_acquisition.return_value = {"state": "RUNNING"}
    window.pages[4].real_start.click()
    work, done = jobs.pop()
    result = work()
    fake_api.start_bound_acquisition.assert_called_once_with("s-bound")
    callback = Mock()
    monkeypatch.setattr(window, "_sim_changed", callback)
    done(result)
    callback.assert_called_once_with("Connected adapter acquisition started")


def test_test_results_have_one_visible_submission_path(window_factory,monkeypatch):
    from PySide6.QtWidgets import QPushButton
    window=window_factory()
    page=window.pages[6]
    window.decision={'candidates':[{'test_id':'test-one','name':'Check voltage','purpose':'Measure voltage'}]}
    page.refresh()
    assert page.result.isHidden()
    assert not any(button.text() == 'Record selected result' for button in page.findChildren(QPushButton))
    record=Mock()
    monkeypatch.setattr(window,'record_selected_test',record)
    fail=next(button for button in page.findChildren(QPushButton) if button.text() == 'FAIL')
    fail.click()
    record.assert_called_once_with()
    assert page.result.currentData() == 'FAIL'


def test_backend_channel_labels_replace_hex_titles_but_keep_selection_ids(window_factory):
    window=window_factory()
    grid=window.pages[4].signals
    grid.set_records([{'channel':'0x0C','display_name':'Engine speed','numeric_value':750,'unit':'rpm'},
                      {'channel':'0x05','display_name':'Coolant temperature','numeric_value':90,'unit':'C'}])
    assert grid.cards[0].title() == 'Engine speed'
    assert grid.selectors[0].currentText() == 'Engine speed'
    assert grid.selectors[0].currentData() == '0x0C'
    assert grid.cards[1].title() == 'Coolant temperature'


def test_live_ai_response_refreshes_recommended_tests(window_factory):
    window=window_factory()
    decision={'candidates':[{'test_id':'test-live','name':'Check voltage','purpose':'Measure voltage'}]}
    window._live_ai_done({'ai':{'available':True,'text':'Summary'},'decision':decision})
    assert window.pages[6].list.count() == 1
    assert window.pages[6].list.item(0).data(Qt.UserRole) == 'test-live'


def test_generate_tests_action_uses_backend_analysis_and_plan(window_factory,monkeypatch,fake_api):
    window=window_factory()
    window.session=Session('test-session','READY',window.active_vehicle)
    fake_api.analyze.return_value={'session_id':'test-session','state':'TESTING'}
    fake_api.decision_plan.return_value={'candidates':[{'test_id':'generated','name':'Check voltage','purpose':'Measure voltage'}]}
    jobs=[]
    monkeypatch.setattr(window,'run_worker',lambda work,done:jobs.append((work,done)))
    window.pages[6].generate.click()
    work,done=jobs.pop()
    done(work())
    assert window.pages[6].list.count() == 1
    fake_api.analyze.assert_called_once_with('test-session',language=window.language)


def test_units_convert_display_without_mutating_evidence():
    from apps.desktop.measurement_units import display_records
    raw = [{"numeric_value": 100, "unit": "km/h"}, {"numeric_value": 90, "unit": "C"}]
    shown = display_records(raw, True)
    assert shown[0]["numeric_value"] == pytest.approx(62.137119)
    assert shown[0]["unit"] == "mph"
    assert shown[1]["numeric_value"] == 194
    assert raw[1]["numeric_value"] == 90


def test_live_simulator_inputs_switch_units_and_keep_physical_values(window_factory):
    window = window_factory()
    live = window.pages[4]
    window.settings_store.setValue("unit_system", "us")
    live.refresh()
    assert live.sim_inputs["coolant_c"].value() == 194
    assert live.sim_inputs["speed_kmh"].value() == pytest.approx(24.85, abs=.01)
    window.settings_store.setValue("unit_system", "metric")
    live.refresh()
    assert live.sim_inputs["coolant_c"].value() == 90


def test_channel_order_does_not_shift_when_record_window_rotates(window_factory):
    grid = window_factory().pages[4].signals
    records = [{"channel": key, "numeric_value": 1} for key in ["0x0C", "0x05", "0x0D", "0x11"]]
    grid.set_records(records)
    before = [s.currentData() for s in grid.selectors]
    grid.set_records(records[1:] + records[:1])
    assert [s.currentData() for s in grid.selectors] == before
    assert len(set(before)) == 4


@pytest.mark.parametrize("port", ["COM3", "COM4", "/dev/ttyUSB0"])
def test_usb_selection_and_connect_send_serial_port_not_wifi_number(window_factory, monkeypatch, fake_api, port):
    window = window_factory()
    window.devices = [{"device_id": "usb-real", "connection_type": "USB", "metadata": {"port": port}}]
    window.selected_device_id = "usb-real"
    page = window.pages[2]
    page.refresh()
    assert page.serial_port.text() == port
    assert not page.port.isEnabled()
    assert page.config() == {"port": port, "baudrate": 115200}
    jobs = []
    monkeypatch.setattr(window, "run_worker", lambda work, done: jobs.append(work))
    window.connect_selected_device()
    jobs[0]()
    fake_api.connect_device.assert_called_once_with("usb-real", {"port": port, "baudrate": 115200})


def test_vehicle_selection_during_list_replacement_ignores_stale_index(window_factory):
    window = window_factory()
    page = window.pages[1]
    page.refresh()
    item = page.list.item(0)
    item.setData(Qt.UserRole, 999)
    page.show_selected()
    assert not page.edit_btn.isEnabled()
    window.vehicles = []
    page.refresh()
    assert page.list.count() == 0
    assert not page.delete_btn.isEnabled()


def test_added_widget_populates_names_and_renders_analog_values(window_factory, qapp):
    grid = window_factory().pages[4].signals
    records = [{'channel': key, 'numeric_value': value, 'unit': unit} for key, value, unit in [
        ('0x0C', 750, 'rpm'), ('0x0D', 40, 'km/h'), ('0x11', 32, '%'),
        ('0x0B', 45, 'kPa'), ('0x05', 90, 'C')]]
    grid.set_records(records)
    grid.add_widget()
    card = grid.cards[-1]
    assert len(grid.cards) == 5
    assert card.title() == 'Coolant temperature'
    assert grid.selectors[-1].currentData() == '0x05'
    assert grid.selectors[-1].currentText() == 'Coolant temperature'
    assert card.gauge.value == 90
    assert card.gauge.scale() == (-40, 160)
    assert not card.gauge.grab().isNull()
    grid.settings.setValue('telemetry_display_mode', 'chart')
    grid.apply_display_mode()
    assert card.gauge.isHidden()
    assert not card.trace.isHidden()
    assert grid.settings.value('telemetry_display_mode') == 'chart'
    grid.set_records(records)
    assert card.title() == 'Coolant temperature'


def test_backend_label_arriving_after_raw_samples_updates_selector(window_factory):
    grid = window_factory().pages[4].signals
    grid.set_records([{'channel': '0x05', 'numeric_value': 90, 'unit': 'C'}])
    assert grid.selectors[0].currentText() == 'Coolant temperature'
    grid.set_records([{'channel': '0x05', 'display_name': 'Custom temperature', 'numeric_value': 91, 'unit': 'C'}])
    assert grid.selectors[0].currentText() == 'Custom temperature'


def test_offline_channel_labels_match_backend_registry():
    from apps.desktop.channel_labels import CHANNEL_LABELS
    from telemetry.channels import _NAMES
    assert CHANNEL_LABELS == _NAMES


def test_window_closes_promptly_during_blocked_session_request(window_factory, monkeypatch, qapp):
    import threading
    import time
    from apps.desktop.api_client import DiagnosticApiClient
    window = window_factory()
    # api_client is independent of ui.DiagnosticApiClient's fixture factory.
    client = DiagnosticApiClient(timeout=300)
    window.api = client
    entered = threading.Event()
    release = threading.Event()
    callbacks = []
    def blocked(*args, **kwargs):
        entered.set()
        release.wait(5)
        raise RuntimeError('late HTTP failure')
    monkeypatch.setattr(client.session, 'request', blocked)
    window.run_worker(lambda: client.create_session({}), callbacks.append)
    try:
        assert entered.wait(1)
        started = time.monotonic()
        window.close()
        while window.isVisible() and time.monotonic() - started < 1:
            qapp.processEvents()
            time.sleep(.005)
        assert not window.isVisible()
        assert not window._workers
        assert callbacks == []
    finally:
        release.set()
        deadline = time.monotonic() + 2
        while window._workers and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(.005)


def test_analog_widgets_fit_inside_cards_in_short_live_data_window(window_factory, qapp):
    window = window_factory()
    window.resize(1100, 650)
    window.nav.setCurrentRow(4)
    qapp.processEvents()
    live = window.pages[4]
    for card in live.signals.cards:
        card.set_display_mode('analog')
    qapp.processEvents()
    for card in live.signals.cards:
        assert card.height() >= 360
        assert card.gauge.height() >= 160
        assert card.gauge.geometry().bottom() < card.contentsRect().bottom()
        assert len(card.findChildren(ui.QComboBox)) == 1
    assert live.signals.height() >= sum(live.signals.cards[i].height() for i in (0, 2))
    assert live.signals.cards[0].gauge.scale() == (0, 8000)


def test_border_drag_grows_and_shrinks_card_and_restores_without_controls(window_factory, qapp):
    from PySide6.QtCore import QPointF, QEvent
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication, QSlider
    from apps.desktop.demo_ui import SignalGrid
    window = window_factory()
    window.nav.setCurrentRow(4)
    qapp.processEvents()
    grid = window.pages[4].signals
    card = grid.cards[0]
    def drag(dx, dy):
        local = QPointF(card.width()-2, card.height()-2)
        position = QPointF(card.mapToGlobal(local.toPoint()))
        QApplication.sendEvent(card, QMouseEvent(QEvent.MouseButtonPress, local, position, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
        QApplication.sendEvent(card, QMouseEvent(QEvent.MouseMove, local+QPointF(dx,dy), position+QPointF(dx,dy), Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        QApplication.sendEvent(card, QMouseEvent(QEvent.MouseButtonRelease, local+QPointF(dx,dy), position+QPointF(dx,dy), Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
        qapp.processEvents()
    before = card.size()
    drag(80, 100)
    assert card.width() == before.width()+80
    assert card.height() == before.height()+100
    drag(-30, -40)
    assert card.width() == before.width()+50
    assert card.height() == before.height()+60
    assert not grid.findChildren(QSlider)
    assert not card.findChildren(QPushButton)
    saved = window.settings_store.value('live_edge_size_0')
    restored = SignalGrid(window.settings_store, prefix='live')
    assert [restored.cards[0].width(),restored.cards[0].height()] == saved
    restored.deleteLater()
    drag(-5000,-5000)
    assert card.height() >= card.minimumSizeHint().height()
    assert card.width() >= 280


def test_settings_selects_display_for_all_widgets_and_preserves_size(window_factory, monkeypatch, qapp):
    window = window_factory()
    live = window.pages[4].signals
    live.cards[0].restore_size([540,480])
    before = live.cards[0].size()
    def choose_chart(dialog):
        mode = next(combo for combo in dialog.findChildren(ui.QComboBox) if combo.findData('chart') >= 0)
        mode.setCurrentIndex(mode.findData('chart'))
        return ui.QDialog.Accepted
    monkeypatch.setattr(ui.QDialog,'exec',choose_chart)
    window._open_settings()
    assert window.settings_store.value('telemetry_display_mode') == 'chart'
    for grid in (window.pages[0].signals, live):
        for card in grid.cards:
            assert card.display_mode == 'chart'
            assert card.gauge.isHidden()
            assert not card.trace.isHidden()
            assert len(card.findChildren(ui.QComboBox)) == 1
    assert live.cards[0].size() == before
    from apps.desktop.demo_ui import SignalGrid
    restored = SignalGrid(window.settings_store, 'live')
    assert restored.cards[0].display_mode == 'chart'
    restored.deleteLater()
