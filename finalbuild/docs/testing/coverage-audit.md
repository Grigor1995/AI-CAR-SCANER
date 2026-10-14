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


## Latest combined coverage after batch 4 — local result (2026-10-14)

The developer-provided output after rerunning the main suite and appending the Desktop test-folder suite reports:

```text
Desktop test-folder suite: 89 passed in 12.10s
TOTAL: 7326 statements, 813 missed, 89% (terminal rounding)
Combined coverage from JSON: 88.90%
Measured source files below 70%: 2
HTML: htmlcov-coverage-audit
XML: coverage-python-audit.xml
JSON: coverage-python-audit.json
```

Compared with the preceding 88.46% snapshot, combined scoped coverage increased to **88.90%** and the number of measured files below 70% decreased from 9 to **2**. The count and percentage are scoped to the configured Python production roots; this is not native iOS/Android coverage or whole-repository coverage.

The names of the remaining two files were not included in the supplied output. Use the JSON report to print their names, exact percentages and uncovered lines before choosing the next test batch.


## Desktop UI/startup coverage expansion — batch 5 (2026-10-14; awaiting local validation)

The last combined JSON report identified only these two files below 70%:

- `apps/desktop/main.py`: 57.03%, 110/256 statements missed.
- `apps/desktop/ui.py`: 68.00%, 273/853 statements missed.

Added test coverage for their untested runtime paths:

- New `apps/desktop/tests/test_main_lifecycle.py`: local backend health/startup and stop behavior; remote-backend startup bypass; occupied ports; source vs frozen startup path; subprocess creation failures; child-process early exit and timeout; log handle cleanup; LLM server health, timeout and early-exit paths; and app-run cleanup after UI close or backend startup failure.
- Expanded `apps/desktop/tests/test_ui_pom.py`: settings save/cancel; add/delete vehicle outcomes; translation and offline catalog fallback; health/device actions and callbacks; DTC-only analysis; session reset; simulator and telemetry guards; AI live-data available/unavailable/error states; device read-outs; live-data polling/refresh and duplicate-request protection; active ECU probe IDs; source/frozen resource resolution; and UI process startup with/without optional icon assets plus the Windows taskbar-icon null-icon guard.

Also corrected a behavior surfaced while testing the live-data provider error path: `LiveDataPage.refresh()` now preserves the “AI: unavailable” message when provider status fetch fails, instead of immediately overwriting it with a generic offline message.

These additions have been pushed to `main` but have **not yet been confirmed by a local test run**. From `finalbuild/`, first run the focused tests:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q \
  apps/desktop/tests/test_main_lifecycle.py \
  apps/desktop/tests/test_ui_pom.py
```

If they pass, rerun the existing clean Step 1 → append Step 2 → Step 3 coverage workflow. In Step 1, `tests/` will include the new backend test suite. In Step 2, `apps/desktop/tests/` will include the new startup/UI cases while continuing to ignore the known native Qt teardown case `test_ui_widgets.py`. Report the new percentage and remaining source files below 70%; do not assume either file passed 70% until measured.


### Batch 5 first local run and test-fixture correction (2026-10-14)

The developer's first focused run reported **84 passed, 1 failed**. The only failure was `test_start_backend_reports_process_exit_during_startup`: its shared helper reset the mocked process's `poll.return_value` to `None` (running), overwriting the intended exit code `2`. The test now restores `poll.return_value = 2` after helper setup so it actually exercises the early-exit branch. This is a test-only correction; production startup behavior was not changed for this failure.

The corrected focused suite still needs to be rerun locally before batch 5 can be marked PASS or a new coverage percentage reported.

## Latest combined coverage result and new target (2026-10-14)

The developer's latest local coverage JSON reports:

```text
Combined coverage: 92.47%
Measured source files below 80%: 8
```

The overall scoped Python coverage is now above 90%. The next task is to raise **each active production source file below 80% to at least 80%**, prioritizing uncovered business logic, error handling and meaningful conditional branches. Do not infer which files remain under the threshold from older audit tables; those percentages predate the latest test batches.

Print the exact current targets and their missing executable lines from `finalbuild/`:

```bash
python - <<'PY'
import json
from pathlib import Path

report = Path("coverage-python-audit.json")
if not report.is_file():
    raise SystemExit("Missing coverage-python-audit.json; rerun the clean Step 1 -> Step 2 workflow first.")

data = json.loads(report.read_text(encoding="utf-8"))
print(f"Combined scoped coverage: {data['totals']['percent_covered']:.2f}%")
low = []
for filename, item in data["files"].items():
    summary = item["summary"]
    statements = summary.get("num_statements", 0)
    percent = summary.get("percent_covered", 0.0)
    if statements and percent < 80.0:
        low.append((percent, filename, summary, item.get("missing_lines", [])))

print(f"Files below 80%: {len(low)}")
for percent, filename, summary, lines in sorted(low):
    print(
        f"{percent:6.2f}% | {filename} | "
        f"covered={summary.get('covered_lines', 0)}/"
        f"{summary.get('num_statements', 0)} | "
        f"missing={summary.get('missing_lines', 0)} | "
        f"lines={','.join(map(str, lines))}"
    )
PY
```

After reviewing this current list, add or extend focused tests for the lowest-coverage active modules first. Re-run the relevant targeted tests locally before recording each batch as passing, then regenerate the combined coverage report. Do not count this scoped percentage as iOS, Android, or whole-repository coverage.

## Per-file 80% coverage expansion — batch 6 (2026-10-14; awaiting local validation)

The latest local coverage JSON is **92.47% combined scoped Python coverage**, with eight measured production files below 80%. Added focused tests for the current list rather than changing the coverage scope:

- `tests/ai/test_low_coverage_ingestion_pipeline.py`: ingestion metadata defaults/overrides, empty-document policy, no-chunk warning, directory suffix filtering and ordering, manifest serialization.
- `tests/ai/test_low_coverage_reasoning_pipeline.py`: evidence-derived vs explicit retrieval query, reranking, prompt assembly and empty retrieval results.
- `tests/diagnostic/test_low_coverage_session_persistence.py`: disabled mode, SQLite insert/update/upsert and reload, invalid-row skip/logging, database read/write error handling and engine disposal.
- `tests/ai/test_low_coverage_reranker.py`: lexical matching/sorting/limits, optional cross-encoder lazy load/cache, prediction order, dependency failure and provider aliases.
- `tests/professional_platform/test_low_coverage_rbac.py`: inactive/insufficient memberships and permission boundaries for viewer, technician, admin and owner.
- `tests/vehicle/test_low_coverage_acquisition_sources.py`: OBD successful/unknown/error PIDs, CAN timeout/frame metadata, UDS decoding and exception records.
- `tests/test_low_coverage_seed_vehicle_catalog.py`: stable IDs, year range validation/normalization, row expansion/defaults and database seeding flow via fakes.
- `tests/api/test_low_coverage_intelligence_routes.py`: session-not-found responses, text evidence ingestion, analysis language localization, PASS/FAIL/INCOMPLETE validation and legacy UNKNOWN normalization.

All new tests are committed on `main`. The developer has now confirmed that the targeted Batch 6 run **passed** locally; the exact test count and elapsed time were not included in the confirmation. This establishes that the new targeted tests pass, but it does not establish the new per-file coverage percentages. Continue with a fresh combined coverage measurement below.

```bash
python -m pytest -q \
  tests/ai/test_low_coverage_ingestion_pipeline.py \
  tests/ai/test_low_coverage_reasoning_pipeline.py \
  tests/diagnostic/test_low_coverage_session_persistence.py \
  tests/ai/test_low_coverage_reranker.py \
  tests/professional_platform/test_low_coverage_rbac.py \
  tests/vehicle/test_low_coverage_acquisition_sources.py \
  tests/test_low_coverage_seed_vehicle_catalog.py \
  tests/api/test_low_coverage_intelligence_routes.py
```

When the targeted batch passes, rerun the clean Step 1 -> append Step 2 -> Step 3 workflow above. Then print every file below 80% with its exact new coverage and missing lines. Overall coverage is already above 90%; the acceptance target now is to bring each active production file below 80% to at least 80%, while preserving meaningful production behavior and the existing scoped denominator.

## Per-file 90% coverage expansion — batch 7 (2026-10-14; awaiting local validation)

The latest local report says overall scoped Python coverage is **92.47%**, while 24 measured production files remain below the new per-file minimum of **90%**. The next goal is to raise those files to at least 90% each without changing the configured production scope or weakening assertions.

Added focused test modules and extended Desktop tests for the latest below-90 list:

- `tests/api/test_low_coverage_network_discovery_routes.py`: passive CAN-frame ingest, invalid hex, missing sessions, map and reset.
- `tests/api/test_low_coverage_multi_bus_routes.py`: connect success/invalid topology, topology lookup, identify-all and DTC reads.
- `tests/api/test_low_coverage_active_discovery.py`: candidate filtering, gateway routing/correlation, active/passive statuses, route errors and policy validation.
- `tests/test_low_coverage_small_modules.py`: Android OTA manifest and health policy, UDS DTC decoder, structured evidence extraction and CAN simulator hooks.
- `tests/vehicle/test_low_coverage_uds_simulator.py`: positive/negative UDS responses, unsupported IDs/services, DTC payloads, multi-frame responses and legacy processing.
- `tests/vehicle/test_low_coverage_multiplexer.py`: CAN response routing, timeouts, repeated start/stop, unmatched-frame retention and channel cleanup.
- `tests/api/test_low_coverage_simple_routes.py`: platform roles/audit and acquisition API request validation, error translation, status and record serialization.
- `tests/vehicle/test_low_coverage_acquisition_manager.py`: connect retries, failure state, poll/reconnect, sink errors, durable offline queueing and stop.
- `tests/vehicle/test_low_coverage_vehicle_diagnostic_service.py`: simulator-only contract, connect/disconnect/reconnect, identity, DTCs, trace and disconnected guards.
- `tests/test_low_coverage_acquisition_api_service.py`: simulator polling, telemetry writes, idempotent start, stop and telemetry error handling.
- `tests/api/test_low_coverage_telemetry_routes.py` and `tests/ai/test_low_coverage_live_analysis.py`: telemetry route guards, evidence deduplication, context bounds and LLM fallback.
- `tests/diagnostic/test_low_coverage_localization.py`: language aliases, unknown-value fallbacks, detailed/legacy test results, recommendation and audit-question translations without mutating the source session.
- `tests/api/test_low_coverage_main_endpoints.py`: session CRUD, vehicle/symptom/DTC updates, evidence synchronization and compatibility analysis/recommendation merging.
- `tests/vehicle/test_low_coverage_multibus_runtime.py`: bus validation, direct and gateway-routed ECUs, ECU identity, DTC read and disconnected runtime.
- `apps/desktop/tests/test_main_coverage_edges.py`: URL health results/errors, model/server resolution, disabled/missing/busy local LLM and launcher cleanup.
- `apps/desktop/tests/test_prepare_windows_icon_coverage.py`: missing icon, image resize and generated WEBP/PNG/ICO validation.
- Extended `apps/desktop/tests/test_ui_pom.py` for invalid/offline vehicle catalog, telemetry refresh errors/stale sessions/success and AI unavailable/success UI states.
- Updated `vehicle/adapters/can_simulator.py` to close an async RX-hook coroutine if synchronous injection happens without a running event loop, preventing an un-awaited coroutine warning; `tests/test_low_coverage_small_modules.py` covers that fallback.

The new core Batch 7 tests are committed on `main` but remain **awaiting local validation**. The developer has now confirmed that the Desktop-specific command passed **95 tests in 13.32s**, and the two previously failing cases passed together (**2 passed in 3.82s**). These results validate the Desktop target command only; they do not yet validate the core Batch 7 tests below. Pull latest `main` and run:

```bash
python -m pytest -q \
  tests/api/test_low_coverage_network_discovery_routes.py \
  tests/api/test_low_coverage_multi_bus_routes.py \
  tests/api/test_low_coverage_active_discovery.py \
  tests/test_low_coverage_small_modules.py \
  tests/vehicle/test_low_coverage_uds_simulator.py \
  tests/vehicle/test_low_coverage_multiplexer.py \
  tests/api/test_low_coverage_simple_routes.py \
  tests/vehicle/test_low_coverage_acquisition_manager.py \
  tests/vehicle/test_low_coverage_vehicle_diagnostic_service.py \
  tests/test_low_coverage_acquisition_api_service.py \
  tests/api/test_low_coverage_telemetry_routes.py \
  tests/ai/test_low_coverage_live_analysis.py \
  tests/diagnostic/test_low_coverage_localization.py \
  tests/api/test_low_coverage_main_endpoints.py \
  tests/vehicle/test_low_coverage_multibus_runtime.py \
  tests/ai/test_low_coverage_ingestion_pipeline.py \
  tests/ai/test_low_coverage_reasoning_pipeline.py \
  tests/diagnostic/test_low_coverage_session_persistence.py \
  tests/ai/test_low_coverage_reranker.py \
  tests/professional_platform/test_low_coverage_rbac.py \
  tests/vehicle/test_low_coverage_acquisition_sources.py \
  tests/test_low_coverage_seed_vehicle_catalog.py \
  tests/api/test_low_coverage_intelligence_routes.py
```

Then validate Desktop-specific targets, including previous lifecycle cases:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q \
  apps/desktop/tests/test_main_coverage_edges.py \
  apps/desktop/tests/test_prepare_windows_icon_coverage.py \
  apps/desktop/tests/test_main_lifecycle.py \
  apps/desktop/tests/test_ui_pom.py
```

Fix test failures before recording the batch as passing. Once targeted tests pass, rerun the **clean Step 1 -> append Step 2** coverage workflow above and print the fresh list below **90%** using the same JSON script from Step 3, changing the threshold comparison from `70.0` or `80.0` to `90.0`. Combined total coverage alone is not enough: each active production file on the target list must reach 90% or be explicitly reviewed as intentionally platform-dependent/infeasible with an evidence-based reason.

### Print the files still below 90%

After Step 2 has created the fresh combined JSON report, use:

```bash
python - <<'PY'
import json

with open("coverage-python-audit.json", encoding="utf-8") as f:
    data = json.load(f)

print(f"Combined scoped coverage: {data['totals']['percent_covered']:.2f}%")
low = []
for filename, item in data["files"].items():
    summary = item["summary"]
    if summary.get("num_statements", 0) and summary.get("percent_covered", 0.0) < 90.0:
        low.append((summary["percent_covered"], filename, summary, item.get("missing_lines", [])))

print(f"Files below 90%: {len(low)}")
for percent, filename, summary, lines in sorted(low):
    print(
        f"\\n{percent:.2f}% | {filename}"
        f"\\nMissing: {summary.get('missing_lines', 0)}"
        f"\\nLines: {','.join(map(str, lines))}"
    )
PY
```

### Batch 7 initial Desktop validation failure and fixture corrections (2026-10-14)

The developer's first Desktop-targeted run reported **93 passed, 2 failed**. Both failures were test setup/expectation issues:

- `test_icon_builder_resizes_small_source_and_creates_all_desktop_formats`: the test redirected outputs to a temporary `assets/` directory but did not create that directory. The fixture now creates the output directory before calling `icons.main()`.
- `test_vehicle_dialog_handles_api_failure_and_malformed_offline_catalog`: the dialog intentionally preserves curated W211 defaults if the API and offline catalog are unavailable. The test incorrectly expected an empty make combo. It now asserts the documented fallback values (`Mercedes-Benz / E-Class / W211`) while verifying that the external/offline catalog remains empty and the Russian offline notice is displayed.

Both test-only corrections are committed to `main`. The developer reran the two corrected cases and reported **2 passed in 3.82s**, then reran the full Desktop-specific command and reported **95 passed in 13.32s**. The Desktop-specific Batch 7 tests are therefore **PASS**. The core Batch 7 targeted tests remain awaiting local validation and combined coverage has not yet been remeasured after this batch.


### Batch 7 core validation failures and corrections (2026-10-14)

The developer's first run of the targeted core batch reported **87 passed, 5 failed**. The five failures and fixes committed to main are:

- `test_active_probe_validates_session_runtime_and_returns_correlation`: retain the `session` returned by the test setup instead of discarding it before asserting the correlated session ID.
- `test_uds_simulator_queues_single_frame_and_legacy_process_drains_tx`: use actual ISO-TP bytes (`b"\\x50\\x03"`, etc.), not backslash characters followed by hex text.
- `test_routed_channel_send_and_multiple_subscribers_receive_same_response`: use valid two-/three-byte CAN payloads instead of accidentally over-escaped payloads that exceeded the eight-byte CAN limit.
- `test_vehicle_diagnostic_simulator_lifecycle_trace_and_status`: the test exposed a production edge case in `trace(limit=0)`, where Python's `trace[-0:]` returned every event. The service now returns an empty list for non-positive limits while still checking that the session exists.
- `test_analysis_enrichment_covers_unmatched_targets_and_default_risk_cost`: the fake engine marked the matching hypothesis as rejected, so the production analysis correctly excluded it from the active category set. The fixture now leaves the hypothesis `possible` to test the matching-target branch; its expected information gain is then 0.25.

These corrections are committed on main. The developer reran the five previously failing test cases and confirmed **5 passed in 2.09s**. This validates the individual fixes, but the **full core Batch 7 suite still needs a rerun** to confirm the remaining cases together. The Desktop-specific targeted batch separately remains confirmed at **95 passed in 13.32s**. Rerun the full core batch command above before regenerating combined coverage.
