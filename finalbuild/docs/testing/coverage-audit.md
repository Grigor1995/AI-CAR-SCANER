# Local Python Coverage Audit

## Current test baseline

Latest developer-provided local test results, before this coverage measurement:

- Main Python suite: **202 passed, 1 skipped** in 26.80 seconds.
- Desktop UI POM suite: **28 passed** in 3.26 seconds.
- No warning summary was present in the supplied outputs.
- **Coverage percentage has not been measured yet.** Passing tests alone does not establish code coverage.

The main suite and Qt UI suite are intentionally run separately. `pytest.ini` discovers `tests/` by default; the desktop UI tests live under `apps/desktop/tests/` and are invoked explicitly.

## Step 1 — collect a Python source coverage baseline

Run from `finalbuild/` in the activated project virtual environment. The first run measures backend, device/protocol roots and the named Desktop production modules while using the current main suite.

```bash
python -m pytest -q tests \
  --cov=backend \
  --cov=vehicle \
  --cov=device \
  --cov=apps.desktop.api_client \
  --cov=apps.desktop.models \
  --cov=apps.desktop.storage \
  --cov=apps.desktop.main \
  --cov=apps.desktop.backend_worker \
  --cov=apps.desktop.ui \
  --cov=apps.desktop.prepare_windows_icon \
  --cov-report=term-missing \
  --cov-report=json:coverage-python-audit.json
```

## First local baseline — user-provided output (2026-10-14)

After Step 1, the developer's local command reported:

```text
202 passed, 1 skipped in 26.24s
TOTAL: 6471 statements, 1193 missed, 82% coverage
```

This is the first baseline for the scoped roots listed in Step 1, **before** adding the Desktop test-folder run. It is not whole-repository or mobile coverage.

Notable production files below 70% in this baseline:

| Source file | Coverage |
|---|---:|
| `backend/ai/rag/retrieval.py` | 33% |
| `backend/ai/rag/pgvector_hybrid.py` | 34% |
| `apps/desktop/api_client.py` | 44% |
| `backend/api/decision_routes.py` | 44% |
| `backend/ai/llm/factory.py` | 43% |
| `vehicle/obd/adapters/ble.py` | 41% |
| `vehicle/obd/adapters/usb_serial.py` | 41% |
| `backend/ai/llm/openai_compatible.py` | 53% |
| `backend/ai/embeddings/providers.py` | 53% |
| `backend/ai/llm/llama_server.py` | 54% |
| `vehicle/obd/adapters/simulator.py` | 57% |
| `vehicle/obd/adapters/tcp_wifi.py` | 57% |
| `backend/ai/ingestion/parsers.py` | 59% |
| `backend/api/rag_routes.py` | 61% |
| `vehicle/isotp/stack.py` | 62% |
| `backend/api/state.py` | 63% |
| `backend/api/ai_routes.py` | 64% |
| `backend/api/device_routes.py` | 66% |
| `backend/api/multi_ecu_routes.py` | 68% |
| `backend/api/vehicle_diagnostic_routes.py` | 68% |
| `backend/ai/ingestion/pipeline.py` | 70% |

Prioritize testable business logic and failure paths in the LLM/RAG/provider modules, API decision/device/catalog routes, and connection adapters. Some branches that require live PostgreSQL, a physical VCI, or platform-specific DLLs should be covered with suitable fakes/mocks where that still tests meaningful behavior. Do not raise a percentage by hiding legitimate code or excluding active production modules.

## Step 2 — append Desktop tests to the same measurement

Use the **same `--cov` source arguments** and add `--cov-append` so results from the first run are retained. The widget suite known to have a native Qt teardown issue is excluded; the POM tests are included.

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q apps/desktop/tests \
  --ignore=apps/desktop/tests/test_ui_widgets.py \
  --cov=backend \
  --cov=vehicle \
  --cov=device \
  --cov=apps.desktop.api_client \
  --cov=apps.desktop.models \
  --cov=apps.desktop.storage \
  --cov=apps.desktop.main \
  --cov=apps.desktop.backend_worker \
  --cov=apps.desktop.ui \
  --cov=apps.desktop.prepare_windows_icon \
  --cov-append \
  --cov-report=term-missing \
  --cov-report=xml:coverage-python-audit.xml \
  --cov-report=json:coverage-python-audit.json \
  --cov-report=html:htmlcov-coverage-audit
```

After this run, `coverage-python-audit.json` represents the combined measurement for the two test runs. Keep this as a local artifact; do not commit generated coverage output.


### Step 2 local result — user-provided output (2026-10-14)

The Desktop test-folder coverage run reported:

```text
89 passed in 12.89s
TOTAL: 7324 statements, 1398 missed, 81% coverage
HTML: htmlcov-coverage-audit
XML: coverage-python-audit.xml
JSON: coverage-python-audit.json
```

This is the combined result after appending Desktop tests to the Step 1 measurement. It remains scoped to the selected Python roots and does not include the excluded `apps/desktop/tests/test_ui_widgets.py` suite or native Android/iOS coverage.

## Step 3 — list source files below 70%

Run this Bash here-document from the same `finalbuild/` directory. It reads the JSON report and prints the total percentage plus every measured production source file below 70%, including files at 0%.

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("coverage-python-audit.json")
if not path.is_file():
    raise SystemExit("Missing coverage-python-audit.json; complete Steps 1 and 2 first.")

data = json.loads(path.read_text(encoding="utf-8"))
print(f"Combined scoped coverage: {data['totals']['percent_covered']:.2f}%")
low = []
for filename, item in data["files"].items():
    summary = item["summary"]
    statements = summary.get("num_statements", 0)
    if statements and summary.get("percent_covered", 0.0) < 70.0:
        low.append((
            summary.get("percent_covered", 0.0),
            filename,
            statements,
            summary.get("missing_lines", 0),
            item.get("missing_lines", []),
        ))

if not low:
    print("No measured source files are below 70%.")
else:
    print(f"Source files below 70%: {len(low)}")
    for percent, filename, statements, missing_count, lines in sorted(low):
        line_list = ",".join(map(str, lines))
        print(f"{percent:6.2f}% | {filename} | missing statements={missing_count}/{statements} | lines={line_list}")
PY
```

## Low-coverage test expansion — batch 1 (2026-10-14)

Added focused test modules on `main` for the first low-coverage targets:

- `tests/api/test_decision_routes_low_coverage.py`: missing sessions/candidates, HIGH-risk safety confirmation, audit logging, and LOW-risk fallback.
- `tests/ai/test_llm_factory.py`: default and alias selection, environment configuration, placeholder provider, and unsupported provider.
- `tests/vehicle/test_low_coverage_obd_transports.py`: simulator responses, BLE notification/buffering/timeouts, USB serial lifecycle/error paths, and Wi-Fi stream lifecycle/errors; external adapters are faked so no hardware is required.
- `tests/ai/test_low_coverage_rag_retrieval.py`: query expansion, multi-query aggregation/deduplication, reranker mapping/fallback, filters, empty results, and candidate sizing.
- `tests/ai/test_low_coverage_pgvector_hybrid.py`: config, vector serialization, dimension validation, upsert parameters, vector/lexical queries, hybrid fusion, and HNSW/IVFFlat schema configuration using a fake SQLAlchemy engine (no live PostgreSQL needed).

The first developer-provided targeted run reported **40 passed, 7 failed**. The failures were confined to two test-design issues:
- The LLM factory tests patched a classmethod with a lambda that incorrectly expected a bound `cls` argument. The mocks were corrected to zero-argument lambdas.
- The pgvector upsert test expected no transaction to start on dimension validation failure. The implementation opens a transaction before checking each vector; the assertion now verifies the actual contract: no SQL is executed for the invalid embedding.

The corrected targeted rerun reported **47 passed in 1.57 seconds** (user-provided local output, 2026-10-14). The targeted tests pass; the combined coverage percentage still needs to be remeasured from a fresh coverage run.

### Validate the new tests

From `finalbuild/`:

```bash
python -m pytest -q \
  tests/api/test_decision_routes_low_coverage.py \
  tests/ai/test_llm_factory.py \
  tests/ai/test_low_coverage_rag_retrieval.py \
  tests/ai/test_low_coverage_pgvector_hybrid.py \
  tests/vehicle/test_low_coverage_obd_transports.py
```

If that passes, rerun Step 1 from a fresh coverage run, then Step 2 with `--cov-append`, and finally Step 3. This keeps the combined report reproducible instead of mixing stale `.coverage` data.

## How to interpret the result

- This is a **scoped Python audit**, not whole-repository or all-platform coverage. Android and iOS require their own native coverage reports.
- The existing CI 90% backend gate is limited to selected diagnostic, telemetry, multi-ECU, simulator, global-data and AI modules. It is not a 90% whole-project gate.
- The existing desktop 95% gate measures a smaller set of API-client/model/storage modules; it does not mean every Desktop production file has 95% coverage.
- First identify genuine active production files at 0%, then add focused tests for those files and for important uncovered branches. Next raise active production files toward the 70% target and the measured scoped total toward 70%.
- Do not include generated files, test files, obsolete code or intentionally platform-specific files in the production denominator without first confirming they are active.
- No CI is required for this audit. Run locally, then use the JSON summary and low-coverage list to plan the next small batch of tests.
