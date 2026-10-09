# CI & Quality Report — AI-CAR-SCANER

**Report date:** 2026-10-09  
**Repository:** [Grigor1995/AI-CAR-SCANER](https://github.com/Grigor1995/AI-CAR-SCANER)  
**Branch:** `main`  
**Validated merge commit:** `7edbac2a37f1f2428daa82bedd2108d482bea0ef`  
**Merged PR:** [#5 — Expand native iOS diagnostic API and golden-case coverage](https://github.com/Grigor1995/AI-CAR-SCANER/pull/5)

> This report records the post-merge CI evidence for the merge commit above. The main-branch Global CI workflow was still running its Android build when this report was written; therefore Android is explicitly marked **PENDING**, not PASS.

## Executive summary

| Area | Result | Evidence |
|---|---|---|
| Python backend tests | **PASS** | 164 passed, 1 skipped |
| Diagnostic-core coverage gate | **PASS** | 91.56%, required minimum 90% |
| Whole-backend coverage | **75%** | Informational; no 90% whole-backend gate is configured |
| Deterministic analysis performance | **PASS** | p50 0.98 ms; p95 1.01 ms; max 1.51 ms in measured run |
| Python compile check | **PASS** | `python -m compileall backend` |
| Internal import graph | **PASS** | `backend/tools/import_check.py` returned OK |
| Desktop CI checks | **PASS** | Desktop dependencies installed; `apps/desktop/ui.py` and `apps/desktop/main.py` compiled |
| Native iOS tests | **PASS** | 7 tests executed, 0 failures; Xcode reported TEST SUCCEEDED |
| Android debug build | **PENDING at report time** | `./gradlew assembleDebug` was still running |
| Live LLM / live-backend integration | **NOT VERIFIED by this CI run** | The iOS test log shows a localhost:8001 connection attempt; the unit tests themselves passed |

## CI workflow links

- [Global CI #74 — main](https://github.com/Grigor1995/AI-CAR-SCANER/actions/runs/37903207441)
- [Native iOS Tests #30 — main](https://github.com/Grigor1995/AI-CAR-SCANER/actions/runs/37903207402)
- [Merged PR #5](https://github.com/Grigor1995/AI-CAR-SCANER/pull/5)

## Python test and coverage results

The CI runs the test suite, a separate performance harness, whole-backend coverage, and a focused diagnostic-core coverage gate.

| Metric | Result |
|---|---:|
| Test suite | 164 passed, 1 skipped |
| Focused coverage scope | 1,161 statements |
| Focused statements missed | 98 |
| Focused diagnostic/core coverage | **91.56%** |
| Required focused coverage | **90%** |
| Whole-backend coverage | **75%** (4,237 statements; 1,051 missed) |
| Pytest warnings in coverage runs | 8 |

The focused coverage command includes diagnostic, telemetry, multi-ECU, simulator, global data, AI reasoning, ML and live-analysis modules. The configured 90% gate passed. The whole-backend figure is lower because it includes a broader set of modules and is currently informational rather than the configured gate.

### Coverage hotspots to improve

Coverage output identifies lower-covered modules that are sensible candidates for additional tests:

- `backend/diagnostic/intelligence.py`: 0% (3 statements)
- `backend/diagnostic/session_persistence.py`: 70%
- `backend/ai/reasoning/pipeline.py`: 72%
- `backend/diagnostic/localization.py`: 85%
- `backend/ai/reasoning/evidence_extractor.py`: 88%
- `backend/multi_ecu/multibus_runtime.py`: 89%

These are improvement opportunities, not CI failures.

## Performance

The dedicated deterministic-analysis performance harness reported:

| Measurement | Observed | Target | Result |
|---|---:|---:|---|
| p50 | 0.98 ms | — | Recorded |
| p95 | 1.01 ms | < 90 ms | **PASS** |
| Maximum in sample | 1.51 ms | < 90 ms budget | **PASS** |

The measured deterministic analysis p95 is well below the 90 ms target. These numbers describe the deterministic-analysis harness only; they do **not** establish end-to-end latency for live LLM inference, retrieval/RAG, a remote API, or a physical vehicle/OBD connection.

## Native iOS test results

The native iOS workflow completed successfully on the main merge commit.

- **7 XCTest tests executed**
- **0 failures**
- Xcode result: **TEST SUCCEEDED**

Coverage includes vehicle catalog request/decoding, vehicle round-trip, session creation payload, selected-language handling, golden-case uncertainty preservation, HTTP error handling, and invalid base-URL validation.

The golden-case test verifies that the diagnostic output preserves uncertainty for the P0302 LPG misfire scenario instead of claiming an unproven component failure.

## Desktop checks

The desktop job completed successfully:

- Installed `apps/desktop/requirements.txt`
- Compiled `apps/desktop/ui.py`
- Compiled `apps/desktop/main.py`

These are dependency and Python syntax checks. They do not constitute a full interactive GUI or end-user workflow test.

## Android checks

**Status at report generation: PENDING.**

The Android job had successfully checked out the repository, configured Java, and made `gradlew` executable. The step `./gradlew assembleDebug` was still running. No successful build result is claimed here.

Check [Global CI #74](https://github.com/Grigor1995/AI-CAR-SCANER/actions/runs/37903207441) for the final Android result. Update this report after the job completes if the final status differs.

## Warnings and limitations

- Pytest emitted 8 warnings during the coverage run. The log includes SQLite connection `ResourceWarning` messages about unclosed database connections; these should be investigated and cleaned up.
- GitHub Actions emitted Node.js 20 deprecation warnings for actions currently being forced onto Node.js 24, plus Node dependency deprecation warnings.
- iOS logs include an attempted connection to `127.0.0.1:8001`. The XCTest suite passed, but a live backend connection was not validated by these unit tests.
- Live LLM availability, real vehicle/OBD connectivity, end-to-end mobile UI behavior, and end-to-end API latency are not proven by the checks listed above.

## Merge and reproducibility

- PR #5 was merged into `main` using squash merge.
- Merge commit: `7edbac2a37f1f2428daa82bedd2108d482bea0ef`.
- CI run IDs and links above point to the post-merge workflows for that commit.

## Recommended follow-up

1. Confirm the final Android `assembleDebug` result in Global CI #74.
2. Investigate and close SQLite connections that trigger resource warnings.
3. Raise whole-backend coverage over time, starting with the low-coverage modules listed above, while retaining the 90% focused gate.
4. Add/retain separate integration tests for a running backend and live model provider so unit-test success is not mistaken for live-service availability.
