# Desktop Full Test Automation — Windows Python 3.14

## Test layers (real coverage vs gaps)

| Layer | Current automation | Isolation |
| --- | --- | --- |
| Unit/model/storage | Existing tests plus negative persistence tests | pytest process, temp APPDATA |
| API client | Routing, payloads, language, timeouts, HTTP 400–504, malformed JSON | Fake responses, no external requests |
| HTTP contract/integration | Full diagnostic session, DTC, symptoms, analysis, plan, INCOMPLETE result; 404/422/503 | Real HTTP against local mock server |
| UI Page Object Model | Dashboard, vehicle management, devices/VCI, diagnostic, live data, ECU network, tests, Armenian/Russian/English; invalid input and stale callbacks | Qt offscreen, API/storage mocks |
| Qt widgets | Sparkline, metric cards, dialogs, GUI components | Separate Qt subprocess |
| Startup/lifecycle | Backend & LLM autostart errors, port conflicts, worker shutdown | Unit tests, mocked child processes |
| Frozen Windows GUI | Real PyInstaller EXE, Qt startup, mock API health/device discovery, event loop, auto-close, **exit=0** | Windows-only mock service and frozen process |
| Physical OBD + actual vehicle | **Not covered automatically** | Requires hardware-in-the-loop/manual testing |
| Real cloud/LLM/RAG provider | **Not covered by offline Desktop suite** | Separate backend and AI tests |
| Desktop performance | pytest durations recorded; no verified native GUI FPS/SLA gate yet | CI evidence, not a performance claim |

The original UI POM tests already cover negative cases (empty symptom/DTC
input, missing vehicle/device/session, Wi-Fi blank host, backend offline,
stale callbacks, malformed vehicle catalog and pending workers).
The new tests extend the negative matrix with explicit timeout, HTTP
authorization, conflict, server failures, corrupt JSON and data persistence
permissions. The complete CI suite uses **no physical OBD device or live
production API**.

## One command — Git Bash

From `finalbuild/`, with the user's existing **Python 3.14 x64 .venv** activated:

```bash
git pull --ff-only origin main

# Source + mocked API integration + negative + UI POM + widgets
bash scripts/run_full_desktop_qa_git_bash.sh

# Same suite + real production-spec EXE build, mock-API launch + shutdown
bash scripts/run_full_desktop_qa_git_bash.sh --with-exe

# Explicitly enforce a 90% combined Desktop coverage gate (optional until
# initial measured baseline is established; see below).
bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90
```

For focused failure diagnosis:

```bash
python scripts/run_desktop_tests.py --group negative
python scripts/run_desktop_tests.py --group logic
python scripts/run_desktop_tests.py --group ui-pom
python scripts/run_desktop_tests.py --group ui-widgets
```

Each group runs as a separate Python subprocess to isolate native Qt
interpreter teardown and prevent one UI collector crash from hiding other
results. A failing group does **not** block collection/reporting of the next
group, but the overall runner exits nonzero if any group fails.

## Reports

The runner creates files in `finalbuild/desktop-test-reports/`:

- `summary.json`: source test-group PASS/FAIL, exit codes, durations,
  combined measured coverage and configured threshold
- `*-junit.xml`: individual test results (includes negative cases)
- `*.log`: detailed pytest output with ten slowest test durations
- `coverage.xml`, `coverage.json`, `htmlcov/index.html`: combined
  Desktop Python source coverage
- `packaged-baseline-result.json`,
  `packaged-fusion-cleanup-result.json`: real EXE lifecycle reports
- `packaged-*-shutdown.log`: validated startup, event-loop exit, backend
  cleanup checkpoints; `packaged-*-console.log` for native failures

### Coverage gate policy

The **project's target is at least 90%**, but a target is not evidence:
do not claim it has been reached until the combined `coverage.json` result
and platform matrix verify it. The runner defaults to measuring/reporting
coverage without a failing gate (`--min-coverage 0`). After a stable
Windows CI baseline, `--min-coverage 90` or the Git Bash `--coverage-90`
flag is the blocking gate. The separate existing Linux CI job already has a
stricter **95%** gate for `api_client`, `models` and `storage`.

Coverage is *source coverage*, not a promise that all vehicle conditions,
UI actions, Windows native DLLs or physical transport devices are tested.

## Frozen EXE smoke contract

The test harness uses a short-lived local HTTP mock backend
(`/health`, `/api/v1/devices`) and an isolated temporary `APPDATA` folder.
The **actual Windows frozen executable** is launched with
`AI_CAR_TEST_AUTOCLOSE_MS=2500` and writes stage checkpoints to
`AI_CAR_SHUTDOWN_TRACE_PATH`. Both variables are opt-in; ordinary users
are unaffected.

A smoke test is **PASS only if**:

1. The exe exists and launches, the real PySide6 window is shown.
2. Actual HTTP GET requests reach the fake backend health and device endpoints.
3. Qt event loop returns normally, and backend/LLM cleanup completes.
4. The process terminates within 60 seconds with **exit code 0**.

Any Windows access violation/139, Qt shutdown/127, timeout, or missing
checkpoint is FAIL. The test does not silently retry a failed release
with different Qt environment settings. The suite tests a baseline run
and a separately labeled `Fusion + explicit cleanup` variant, whose
results must not be conflated.

Run against an existing EXE:

```bash
python scripts/smoke_test_desktop_exe.py \
  --exe dist-release/icon-preview/AICarScanner.exe
python scripts/smoke_test_desktop_exe.py \
  --exe dist-release/icon-preview/AICarScanner.exe \
  --fusion --explicit-cleanup
```

## Windows GitHub Actions

`.github/workflows/desktop-full-qa.yml` triggers on Desktop-relevant push
to main, pull requests, and manual `workflow_dispatch`.

It installs Python 3.14, runs all four isolated test groups, builds both
bundled executables using the canonical specs, executes real frozen GUI
smoke tests and uploads test/coverage reports. Both source and EXE smoke
errors **fail CI**; no `continue-on-error` on the QA gate.

No job result is represented as PASS until GitHub Actions finishes.


## October 16 Windows results: icon test repaired, coverage gaps visible

The user's new full desktop suite result before these changes:

- `ui-widgets`: **17 passed, 1 failed**; the failing test was
  `test_desktop_icon_assets_are_generated_from_android_launcher`.
- **All-source Desktop coverage: 82.67%** (90% target NOT achieved).
- Overall Desktop QA: **FAIL**.

The failing widget test called the *legacy* `prepare_windows_icon()`
directly in the real tracked `assets/` folder and compared the result
against the Android launcher. That contradicted the newer Windows build
contract, which preserves local edited artwork and stages new PNG/WEBP/ICO
inside `build-release/`. The test now uses an isolated temporary edited
PNG and verifies format parity and input preservation. No real icon is
overwritten by the widget suite.

Added real tests for `backend_worker` source/frozen launch (no real
port), and positive and negative icon verification (corrupt, missing,
mismatched alpha/dimensions/colors, invalid ICO, invalid Windows EXE
resource, Qt decoding failures). These cover meaningful untested paths,
not mock-only line execution.

The automation now reports:

1. **All-source coverage** (same `--cov=apps.desktop` denominator as
   the user's 82.67% baseline). It includes optional tooling, diagnostic
   hooks/probes, the GUI, main, API and supporting scripts.
2. **Production-core coverage** subtotal, covering exactly nine runtime
   modules (`api_client`, `models`, `storage`, `main`,
   `backend_worker`, `ui`, `prepare_windows_icon`,
   `stage_windows_icons`, `verify_icons`). No unreported production
   module is silently excluded from this subtotal; the report lists
   its exact scope.
3. **File-level uncovered statement counts** and line previews in
   `desktop-test-reports/coverage-gaps.json` and the terminal.

These are separate metrics. A 90% production-core PASS does not mean
the *all-source* 90% target has passed.

### Verify from Git Bash (no EXE rebuild needed)

```bash
git pull --ff-only origin main
QT_QPA_PLATFORM=offscreen python -m pytest -q \
  apps/desktop/tests/test_ui_widgets.py \
  apps/desktop/tests/test_verify_icons_negative.py \
  apps/desktop/tests/test_backend_worker_coverage.py

bash scripts/run_full_desktop_qa_git_bash.sh
```

To request independent blocking gates:

```bash
# All measured apps.desktop source, including debugging tooling:
bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90

# Explicitly scoped production runtime only, while also reporting all source:
bash scripts/run_full_desktop_qa_git_bash.sh --core-coverage-90
```

Neither threshold is declared achieved until a fresh Windows coverage
JSON file confirms it. Report `summary.json` and `coverage-gaps.json`
if uncovered modules remain after this batch.
