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

## Combined audit result after batch 1 (2026-10-14)

User-provided local outputs after adding the first focused tests:

```text
Main test suite: 249 passed, 1 skipped in 24.63s
Main-suite scoped coverage: 6471 statements, 1023 missed, 84%
Desktop test-folder suite: 89 passed in 10.43s
Combined scoped coverage: 7324 statements, 1228 missed, 83%
```

The combined scoped result is now **83%**, up from the previous combined baseline of 81%. The Desktop test-folder run displayed non-fatal coverage warnings that `apps.desktop.backend_worker` and `apps.desktop.prepare_windows_icon` were not imported during that run; the combined report still showed those modules because the first test run measured them. Do not confuse these warnings with pytest test failures.

## Low-coverage test expansion — batch 2 (2026-10-14)

Added the following additional focused test modules on `main`:

- `tests/ai/test_low_coverage_embedding_providers.py`: deterministic hash embeddings, optional sentence-transformers and fastembed lazy loading, normalization parameters, import failures, aliases and unsupported providers.
- `tests/ai/test_low_coverage_document_parsers.py`: text/form-feed parsing, JSON and YAML success/fallback, HTML extraction, PDF page handling and missing dependency, unsupported/missing files and custom parser registration.
- `tests/ai/test_low_coverage_openai_compatible.py`: request URL/body/headers, optional authorization, successful response parsing, network/HTTP/timeout/invalid JSON errors.
- `tests/api/test_state_registry_low_coverage.py`: cache/mapping operations, persisted lookup/refresh, writes, and persistence-disabled branches.

The developer's first run of batch 2 reported **32 passed, 1 failed**. The failure was a test assertion using `ParsedPage.number`, but the actual model field is `ParsedPage.page_number`. The assertion was corrected, and the developer subsequently confirmed the batch **passes** (exact count/time were not provided).

### Batch 2 validation command

From `finalbuild/`:

```bash
python -m pytest -q \
  tests/ai/test_low_coverage_embedding_providers.py \
  tests/ai/test_low_coverage_document_parsers.py \
  tests/ai/test_low_coverage_openai_compatible.py \
  tests/api/test_state_registry_low_coverage.py
```


## Low-coverage test expansion — batch 3 (2026-10-14)

Added four more focused test modules to `main`, with no requirement for a live LLM server, real VCI hardware, or a live database:

- `tests/ai/test_low_coverage_llama_server.py`: configuration clamps, auth headers, HTTP/URL errors, model resolution, server context fallback, health/availability, context compaction, generation payloads and malformed/empty inference responses.
- `tests/vehicle/devices/test_low_coverage_connection_manager.py`: USB/BLE discovery via fakes, Wi-Fi probe success/failure, transport factory validation, connection status/error/reconnect and unknown-device paths.
- `tests/vehicle/isotp/test_low_coverage_stack.py`: malformed frames, timeouts, sequence validation, payload constraints, flow-control overflow/wait/block-size, and extended-frame sending.
- `tests/api/test_low_coverage_vehicle_catalog_routes.py`: catalog filtering/facets, resolve queries, blank make/model errors and database-unavailable translation, using mocked query results.

The developer-provided local run confirmed **63 passed in 1.73 seconds** for batch 3 (2026-10-14).

### Batch 3 validation command

```bash
python -m pytest -q \
  tests/ai/test_low_coverage_llama_server.py \
  tests/vehicle/devices/test_low_coverage_connection_manager.py \
  tests/vehicle/isotp/test_low_coverage_stack.py \
  tests/api/test_low_coverage_vehicle_catalog_routes.py
```

## How to interpret the result

- This is a **scoped Python audit**, not whole-repository or all-platform coverage. Android and iOS require their own native coverage reports.
- The existing CI 90% backend gate is limited to selected diagnostic, telemetry, multi-ECU, simulator, global-data and AI modules. It is not a 90% whole-project gate.
- The existing desktop 95% gate measures a smaller set of API-client/model/storage modules; it does not mean every Desktop production file has 95% coverage.
- First identify genuine active production files at 0%, then add focused tests for those files and for important uncovered branches. Next raise active production files toward the 70% target and the measured scoped total toward 70%.
- Do not include generated files, test files, obsolete code or intentionally platform-specific files in the production denominator without first confirming they are active.
- No CI is required for this audit. Run locally, then use the JSON summary and low-coverage list to plan the next small batch of tests.


## Updated combined coverage measurement (2026-10-14)

Latest combined coverage output provided by the developer:

```text
Combined coverage: 88.46%
Files below 70%: 9
```

Files currently reported below 70%:

| Source file | Coverage | Missing statements |
|---|---:|---:|
| `apps/desktop/api_client.py` | 44.12% | 57 |
| `apps/desktop/main.py` | 50.39% | 127 |
| `backend/api/knowledge_routes.py` | 51.52% | 16 |
| `backend/api/rag_routes.py` | 60.71% | 11 |
| `backend/ai/llm/orchestrator.py` | 61.54% | 5 |
| `backend/api/ai_routes.py` | 64.29% | 15 |
| `backend/api/device_routes.py` | 65.85% | 28 |
| `backend/api/vehicle_diagnostic_routes.py` | 67.81% | 47 |
| `backend/api/multi_ecu_routes.py` | 68.06% | 23 |

This is the developer-provided measurement before locally validating the new route-focused test batch below. The two Desktop files remain the next candidates after backend route tests are run; desktop API-client tests already exist under `apps/desktop/tests/test_api_client.py`, so ensure that suite is part of the appended coverage run before interpreting its measured percentage.

## Low-coverage test expansion — batch 4 (2026-10-14; awaiting local validation)

Added focused tests on `main` for:

- `tests/api/test_low_coverage_knowledge_routes.py`: text/file ingestion, temp-file contents and suffixes, title defaults/overrides, metadata validation, serialized response and invalid JSON.
- `tests/api/test_low_coverage_rag_routes.py`: config values/defaults, request validation, successful retrieval serialization, and repository/provider/retriever/timeout failures mapped to 503.
- `tests/ai/test_low_coverage_orchestrator.py`: evidence/context serialization, missing vehicle, supplied retrieval, requested language, and provider prompt/context.
- `tests/api/test_low_coverage_ai_routes.py`: knowledge indexing/search, unknown sessions, requested language, provider config and provider availability branches.
- `tests/api/test_low_coverage_device_routes.py`: device serialization, scanning, Wi-Fi probe, connect/reconnect/disconnect/status, OBD VIN/DTC/live-data and expected error translation.
- `tests/api/test_low_coverage_vehicle_diagnostic_routes.py`: connection lifecycle, ECU identification/DTC reads, trace validation, binding, OBD sync, evidence/audit updates, deduplication and error paths.
- `tests/api/test_low_coverage_multi_ecu_routes.py`: connect/disconnect, topology, identify-all, read-all DTCs/correlation, trace validation and runtime errors.

The new modules have **not yet been confirmed by a local pytest run**. Validate them from `finalbuild/`:

```bash
python -m pytest -q \
  tests/api/test_low_coverage_knowledge_routes.py \
  tests/api/test_low_coverage_rag_routes.py \
  tests/ai/test_low_coverage_orchestrator.py \
  tests/api/test_low_coverage_ai_routes.py \
  tests/api/test_low_coverage_device_routes.py \
  tests/api/test_low_coverage_vehicle_diagnostic_routes.py \
  tests/api/test_low_coverage_multi_ecu_routes.py
```

After resolving any failures, rerun the full Step 1 coverage command from a clean measurement, then the Step 2 Desktop run with `--cov-append`, and finally Step 3. Do not treat the current 88.46% as the post-batch-4 percentage until those measurement steps have been repeated.


### Batch 4 first local run and corrective changes (2026-10-14)

The first reported run returned **73 passed, 11 failed**. The failing cases identified two separate causes:

1. **Windows temporary-file sharing:** the direct unit test exposed that the text-ingestion route passed a still-open `NamedTemporaryFile` path into the pipeline. This can prevent the pipeline from reopening the file on Windows. The route now writes a regular file inside `TemporaryDirectory`, closes it before calling the pipeline, and cleans it up on exit. Both text and upload ingestion use this pattern.
2. **Direct handler invocation defaults:** outside FastAPI request processing, parameters declared as `Form("{}")` and `Form(None)` are FastAPI parameter objects, not the runtime strings/None. File-ingestion unit tests now pass `metadata_json="{}"` and `title=None` explicitly.
3. **RAG config mock signature:** `PgVectorConfig.from_env` is a classmethod, but monkeypatch replaces its descriptor with a plain function. The mock must therefore be `lambda: cfg`, not `lambda _cls: cfg`.

These changes are committed to `main`. The corrected batch has **not yet been rerun**, so do not record it as passing until the next local pytest result confirms it.


### Batch 4 corrected local validation — PASS (2026-10-14)

The developer reran all seven batch 4 modules after the fixes above. The supplied local result is:

```text
84 passed in 1.81s
```

This confirms the targeted batch 4 test modules pass in the developer's local environment. The total combined coverage has **not yet been remeasured after batch 4**; rerun the clean Step 1 → append Step 2 → JSON Step 3 workflow before recording a new coverage percentage.
