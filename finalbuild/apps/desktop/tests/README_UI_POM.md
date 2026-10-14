# Desktop UI Page Object Model tests

These tests exercise the PySide6 UI without calling the live backend, connecting to a vehicle, or changing real vehicle data. API and storage boundaries are replaced with test doubles in the test fixture.

## Run locally (no CI)

Run commands from the `finalbuild/` directory, with the project virtual environment activated.

```bash
# Qt widgets in headless/offscreen mode
QT_QPA_PLATFORM=offscreen python -m pytest -q apps/desktop/tests/test_ui_pom.py

# UI-only coverage report
QT_QPA_PLATFORM=offscreen python -m pytest -q apps/desktop/tests/test_ui_pom.py \
  --cov=apps.desktop.ui --cov-report=term-missing --cov-report=html:htmlcov-ui

# Existing local regression suite
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

The full regression suite can skip integration tests that require external services (for example PostgreSQL/pgvector). Qt/PySide6 UI tests are intentionally stored under `apps/desktop/tests/` and run separately from the default `tests/` discovery, avoiding native Qt import crashes during combined collection on affected Windows/Python environments. The UI POM suite itself does not require a running API server or physical VCI device.

## Page Object Model

`test_ui_pom.py` keeps UI access behind page objects:

- `DashboardPO`: backend, selected vehicle, session, ECU metrics and refresh action.
- `VehiclesPO`: local vehicle list, selection, details and delete state.
- `DiagnosticPO`: symptom/DTC entry, analysis submission, evidence, hypotheses and questions.
- `LiveDataPO`: acquisition status, telemetry table, chart values and timer.
- `ResultsPageObject`: candidate selection, canonical PASS/FAIL/INCOMPLETE values and technician notes.
- `DevicesPO`: VCI selection and Wi-Fi/USB/BLE connection configuration.
- `NetworkPO`: passive ECU candidates and active probe correlation.

The tests also cover the vehicle dialog, language switching, worker success/error signals, sparkline/metric widgets, validation of empty inputs, session creation, telemetry refresh deduplication and stale-response protection, diagnostic test result submission, and device callbacks.

## Isolation and safety

- API and storage are mocked; no network service is required.
- Qt is configured for `offscreen` mode for local headless execution.
- Tests do not require CI to run.
- Coverage output is local evidence only; it is not a claim that the suite has passed on every operating system.
