# AI-CAR-SCANER — Repository Audit and Release Readiness Report

Audit date: 2026-10-13  
Repository: Grigor1995/AI-CAR-SCANER  
Branch reviewed: main  
Base commit reviewed: 36dd6bddb946c56ca3dafe44d1bd6b11b9817f84  
Audit method: GitHub source/tree review, static architecture inspection, targeted changes; no cloud CI and no project tests executed.

## A. Executive summary

The current main branch is a real multi-platform automotive diagnostic project, not a Flutter application. It contains a FastAPI/Python backend, deterministic diagnostic rules, optional AI/RAG and local LLM interfaces, OBD/CAN/ISO-TP/UDS/VCI abstractions, telemetry and network discovery modules, a PySide6 desktop client, a Kotlin/Jetpack Compose Android client, a SwiftUI iOS client, data catalogs, structured tests, and architecture documentation.

Release decision: NOT RELEASE-READY. Useful diagnostic/domain boundaries and regression tests exist, but runtime verification is missing for this audit, and several security, data consistency, persistence scaling, offline-state, and packaging risks remain.

Changes included in this audit commit:
- Fixed a Windows PyInstaller backend-spec root path that pointed at the wrong directory.
- Reworked the standalone Windows build scripts to use the one-file executable layout actually defined by the specs, separate output into dist-release/build-release, check tool exit codes, and preserve the pre-existing dist directory.
- Made the default desktop backend URL follow AI_CAR_BACKEND_PORT unless AI_CAR_BACKEND_URL is explicitly set.
- Restored RGB pixel comparison in the icon parity test so matching alpha channels cannot conceal different RGB pixels.
- Strengthened the LPG_MISFIRE_001 regression contract to require every canonical expected hypothesis domain, reject the specified unsupported conclusions, and require an LPG-specific diagnostic action.
- Added a regression test for a custom desktop backend port.
- Added ignore rules for generated executables/build outputs, per-machine Android SDK configuration, and transient FETCH_HEAD metadata.
- Removed the tracked generated Windows executable, the per-machine Android local.properties file, and the empty FETCH_HEAD from the current tree. Git history was not rewritten. The generated executable must be rebuilt from source.

These are source-level changes. The relevant tests/builds have NOT been run in this environment, so the fixes are not being claimed as runtime-verified. Cloud CI was not triggered or rerun, in accordance with the payment constraint.

## B. Repository inventory and architecture

The base source tree contained 392 file blobs in 137 directories (529 tree entries including directories). The inventory includes 279 Python files, 16 Kotlin files, 8 Swift files, and roughly 70 test-named files across Python, Swift and platform test locations.

| Component | Source directory | Responsibility | Verification in this audit |
|---|---|---|---|
| API application and routes | finalbuild/backend/api/ | Session CRUD, analysis, catalog, intelligence, telemetry, acquisition, device/VCI and discovery endpoints | Static review only |
| Diagnostic domain and rules | finalbuild/backend/diagnostic/ | DiagnosticSession, evidence, hypotheses, rules, decisions, localization, persistence | Static review only |
| AI and RAG | finalbuild/backend/ai/ | Evidence extraction, reasoning orchestration, LLM provider interfaces, ingestion, retrieval and grounding | Static review only; no model/RAG runtime |
| Vehicle protocols/adapters | finalbuild/vehicle/ and finalbuild/backend/vehicle/ | OBD, CAN, ISO-TP, UDS, J2534 boundaries, discovery and simulator adapters | Static review only; no physical VCI |
| Telemetry and multi-ECU | finalbuild/backend/telemetry/ and finalbuild/backend/multi_ecu/ | Signal collection/analysis, bus and ECU orchestration | Static review only |
| Device/service layer | finalbuild/device/ and finalbuild/backend/device/ | Device abstraction, local store, sync queue and service seams | Static review only |
| Vehicle/global data | finalbuild/data/, finalbuild/shared/, finalbuild/backend/global_data.py | Curated fitment, broad catalog, offline selector data and diagnostic cases | Static review only; duplication identified |
| Desktop | finalbuild/apps/desktop/ | PySide6 UI, API client, process startup, LLM launch and packaging | No UI or packaged executable launched |
| Android | finalbuild/apps/mobile-android/ | Native Kotlin/Jetpack Compose, API/repository/ViewModel and transport foundations | No Gradle or emulator run |
| iOS | finalbuild/apps/mobile-ios/ | Native SwiftUI app, API client/models and XCTest contracts | No Xcode/simulator run |
| Backend/domain tests | finalbuild/tests/ | AI, API, catalog, harness, performance, security, telemetry, vehicle protocol and regression tests | Not run |
| Desktop tests | finalbuild/apps/desktop/tests/ and test_smoke.py | UI widgets, client, storage, main helpers and flows | Not run |
| Android tests | finalbuild/apps/mobile-android/app/src/test/ | API/repository unit contracts | Not run |
| iOS tests | finalbuild/apps/mobile-ios/Tests/ | API, model and error-path tests | Not run |
| Docs | finalbuild/docs/ and finalbuild/PLATFORM_FEATURE_PARITY.md | Architecture, hierarchy, dependencies, data flow and parity gaps | Reviewed; known gaps remain |

### Architecture and flow

~~~mermaid
flowchart TD
  D[PySide6 Desktop] --> API[FastAPI]
  A[Kotlin Android] --> API
  I[SwiftUI iOS] --> API
  API --> S[DiagnosticSession and routes]
  S --> R[Deterministic rules]
  S --> E[Evidence and hypotheses]
  S --> P[Session snapshot persistence]
  API --> C[Vehicle catalog API]
  C --> DB[(PostgreSQL catalog)]
  S --> N[Decision and next-test engine]
  API --> AI[Optional AI reasoning]
  AI --> RAG[RAG retrieval and grounding]
  AI --> LLM[Optional local llama-server]
  API --> VCI[OBD, UDS, CAN and VCI services]
  VCI --> SIM[Simulator or supported adapter]
~~~

A strong design choice is that deterministic reasoning is separate from optional AI output. The DiagnosticSession/evidence model and golden-case tests make the application more explainable than a scanner-only or chatbot-only design. Remaining release risks are concentrated in boundaries: API security, session persistence scaling/concurrency, the source of truth for vehicle catalogs, mobile fallback/error states, and desktop packaging.

## C. Defects and risks found

### P1 — Authentication and authorization helpers are not wired into the API boundary

The repository has token verification, RBAC and rate-limit helper modules under backend/security. The reviewed FastAPI application registers routers without a global authentication dependency, and code search did not find runtime uses of verify_token, allowed, or the rate limiter in the API route path. The security tests exercise helpers in isolation; helper tests do not prove endpoints enforce them.

Impact: session mutation, device/VCI, telemetry and discovery endpoints need route-by-route security review before public production deployment.

Next action: implement authentication middleware/dependencies and per-resource/tenant authorization, then test unauthenticated access, role denial, session isolation, and rate limiting. This was not enabled as part of this change because adding enforcement without a compatible login/token path would break current desktop/mobile clients.

### P1 — Session persistence cost grows with the number of sessions

GlobalSessionRegistry reads can refresh/load persisted sessions. The HTTP middleware invokes persist_sessions after each request, and save_all iterates the cached session collection and performs a lookup/write per session. This makes routine API work grow with stored session count and introduces avoidable database traffic. Documentation also identifies last-write-wins behavior for concurrent writes.

Impact: this may become a latency/reliability bottleneck and does not provide explicit optimistic concurrency control.

Next action: target individual session reads/writes, track dirty sessions, make transaction boundaries explicit and add a version/ETag strategy. Measure performance at several stored-session counts. No performance measurement was made in this audit.

### P1 — Catalog/database readiness is not represented by the health endpoint

The vehicle catalog endpoints access PostgreSQL and can return HTTP 503 when the database/table is unavailable. The basic health endpoint still reports status OK without checking catalog readiness or whether catalog rows are seeded. Session persistence can be disabled without DATABASE_URL, while the catalog router uses a PostgreSQL default of its own.

Impact: a local backend can appear healthy and allow an in-memory session while the vehicle catalog does not work.

Next action: keep liveness separate from readiness; document database-required versus in-memory behavior; test missing database, unseeded catalog and unavailable catalog states. Do not convert catalog/API failure into a fake successful result.

### P1 — Windows standalone packaging paths did not agree

The nested backend_service.spec calculated its project root from parents[2], which resolves to the apps directory, not finalbuild. That produced incorrect paths for backend_worker.py and the backend package. The standalone PowerShell builder expected executables inside per-app folders, while the active specs declare one-file outputs named backend_service.exe and AICarScanner.exe. It also deleted the existing dist directory before building.

Change in this commit: the backend spec finds the project root by searching for apps/desktop/backend_worker.py; the canonical builder writes to dist-release and build-release, uses the spec output filenames, checks command exit codes, and does not remove the existing dist directory. The older desktop build entry point delegates to the canonical builder.

Still blocked: the PowerShell scripts and PyInstaller specs were not executed on Windows. The app must still be built/launched and tested with backend available/unavailable, missing model/server, invalid/busy ports and clean shutdown. A build alone will not prove runtime success.

### P1 — Diagnostic metric semantics create false precision

The reasoning engine increments keyword-matched scores and stores them as possible:<score>. This is not a calibrated probability. The analysis route fills some zero/missing costs from a risk-level mapping and derives information gain from category overlap. The Android DTO defaults missing informationGain and estimatedCost to 0.0 and UI code renders those values; iOS requires numeric values too.

Impact: the user may read a heuristic ranking as a probability, or interpret a default zero as a real zero cost/value. The cost metric also lacks an explicit currency/unit.

Next action: define a shared contract for unknown values and units; label the current score as a heuristic ranking or replace it with a validated method; add cross-platform tests showing missing values are not rendered as zero. Not changed in this commit because it requires coordinated API/domain/client changes plus runnable tests.

### P2 — Vehicle catalog has overlapping sources and fallback lists

The repository contains:
- data/vehicle_catalog.json — broad family-level guidance grouped into 30 make records.
- data/vehicle_fitment_catalog.json — 22 curated chassis/model entries with year ranges and engine/ECU/fuel information.
- data/vehicle_fitments.json — 22 entries in an expanded-year representation.
- shared/vehicle_catalog.json — 369 offline selector variants.
- A separate hardcoded native Android catalog in VehicleCatalog.kt.
- iOS primarily relies on the backend and has no equivalent guaranteed offline selector catalog.

There are also two catalog seed scripts that consume different inputs and schemas. These can diverge after future edits.

Next action: choose one authoritative fitment schema, add a deterministic generator for database and offline snapshots, version the result, label stale/offline results, and contract-test all platform consumers. Never treat family-level guidance as VIN-confirmed fitment or invent unknown vehicle specifications.

### P2 — LPG golden-case regression previously checked only a subset of the intended contract

The YAML golden case used legacy category names, while data/global/diagnostic_cases.json uses the canonical categories: LPG fuel delivery / mixture, ignition / combustion, air-fuel / intake, and mechanical cylinder condition. The older YAML regression only required the legacy ignition and intake aliases and rejected a coil phrase; it did not require all expected domains or a relevant follow-up action.

Change in this commit: YAML and regression assertions now use the canonical domains, forbidden claims cover coil/injector/mechanical failure, and the test requires an LPG pressure/injector/fuel-trim diagnostic action.

Still blocked: the updated regression test was not run here.

### P2 — Icon parity assertion could miss RGB differences

The merged test compared an RGBA difference image using getbbox directly. Pillow documents getbbox alpha-only behavior for RGBA; if the alpha channel matches, RGB differences may not be reflected in the bounding box. The assertion now converts the difference image to RGB before getbbox. See the [Pillow Image.getbbox documentation](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.getbbox).

Still blocked: the icon/widget test was not run here.

### P2 — Catalog failures and local fallback are not communicated consistently by mobile clients

Android loadVehicleCatalog catches catalog failures and keeps a local selector without a visible stale/offline indication. iOS converts catalog request errors into an empty list via try? and does not set the visible error state. That conflicts with the documented shared client contract that offline fallbacks must be clearly identified.

Next action: track catalog source/loading/staleness in client state, show an offline/stale badge/message, and test successful, empty, 503 and offline responses.

### P2 — Coverage gates are not equivalent across platforms

The CI configuration uses a 90% threshold for a selected backend module set, not the whole repository. The general backend coverage report has no threshold. Desktop's 95% gate measures selected API-client/model/storage modules; Qt widget tests currently use continue-on-error. Android collects unit coverage without a numeric threshold; iOS coverage has no numeric gate.

Next action: report the measured scope by module, fix flaky UI teardown and make relevant UI checks release-blocking, then set meaningful per-platform gates. No current coverage number was measured.

### P2 — Optional LLM startup failures may not be visible to desktop users

The configured local GGUF model is not present in the tracked models folder (only model instructions). Some startup failures print to stderr while the packaged UI spec sets console=False. Backend child output is logged, but not every local LLM failure is surfaced in a persistent and visible way.

Next action: log startup status and exceptions to a persistent application log, show a visible deterministic-only/offline status, and test missing model, missing server, occupied port and timeout paths.

### P2 — Custom desktop backend port previously left health checks on port 8001

The backend process port was configurable but the default BACKEND_URL remained hard-coded to port 8001. This could start a server on a different port and continue checking the old port.

Change in this commit: default BACKEND_URL is derived from PORT, while explicit AI_CAR_BACKEND_URL still takes precedence. A regression test was added but not executed.

## D. Changes made in this audit commit

| File/path | Change | Verification |
|---|---|---|
| report.md | Consolidated architecture, findings, fixes, test scope and release status | Content reviewed |
| finalbuild/apps/desktop/main.py | Configurable backend port is reflected in default URL | Test added, not run |
| finalbuild/apps/desktop/tests/test_ui_widgets.py | RGB pixel-level icon comparison restored | Test not run |
| finalbuild/apps/desktop/specs/backend_service.spec | Correct project-root discovery for backend bundle | Windows build not run |
| finalbuild/scripts/build_windows_standalone.ps1 | Use actual one-file outputs, isolated output paths and exit-code checks; preserve existing dist | Windows build not run |
| finalbuild/apps/desktop/build_windows.ps1 | Delegate to maintained canonical build script | Windows build not run |
| finalbuild/tests/desktop/test_phase32_ports_and_timeout.py | Custom-port regression added | Test not run |
| finalbuild/datasets/golden-cases/LPG_MISFIRE_001.yaml | Canonical expected categories and forbidden conclusions | Test not run |
| finalbuild/tests/regression/test_golden_case.py | Assert all categories, forbidden claims and LPG-specific action | Test not run |
| finalbuild/.gitignore | Ignore local SDK settings, transient Git metadata and generated executables/build outputs | Static review |
| finalbuild/dist/AICarScanner.exe | Removed generated 58 MB executable from current tree | No replacement built |
| finalbuild/apps/mobile-android/local.properties | Removed machine-specific Windows SDK path | Recreate locally with Android Studio/ANDROID_HOME |
| finalbuild/FETCH_HEAD | Removed empty transient file | Not applicable |

Git history was not rewritten. Removing the generated executable from the current tree does not erase it from previous commits.

## E. Test report

For this audit:
- Backend/domain pytest: NOT RUN.
- Desktop unit/UI tests: NOT RUN.
- Android Gradle unit tests/build: NOT RUN.
- iOS XcodeGen/XCTest: NOT RUN.
- Windows packaging/executable launch: NOT RUN.
- Coverage: NOT MEASURED.
- Performance: NOT MEASURED.
- Cloud CI: NOT triggered or rerun, as requested.

The local clone is not mounted in the tool runtime. An attempted direct Git network read failed because the runtime could not resolve github.com. Source inspection was therefore performed through the GitHub repository connector; runtime pass/fail claims cannot be made.

Existing test scope observed: 64 files under finalbuild/tests, 6 desktop test files, 2 Android unit-test files and 2 iOS XCTest files, plus local-AI script tests. Exact test-function counts, failures, skips and warnings were not produced by a new local run.

Previously discussed counts such as 139 passed/1 skipped, 14 desktop UI tests passed, or an older iOS baseline are historical and do not validate the current main commit or changes in this audit.

### Local commands for PyCharm (instructions only; not executed here)

From finalbuild, in the project's virtual environment:

~~~powershell
python -m pytest -q
python -m pytest -q -s tests/harness/test_performance.py
python -m pytest -q --cov=backend --cov-report=term-missing
python -m pytest -q --cov=backend/diagnostic --cov=backend/telemetry --cov=backend/multi_ecu --cov=backend/simulator --cov=backend/global_data.py --cov=backend/ai/reasoning --cov=backend/ai/ml --cov=backend/ai/live_analysis --cov-report=term-missing --cov-fail-under=90
python -m pytest -q apps/desktop/tests --ignore=apps/desktop/tests/test_ui_widgets.py
~~~

Then test Qt widgets separately:

~~~powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q apps/desktop/tests/test_ui_widgets.py
~~~

Android, with Java 17 and Android SDK configured:

~~~powershell
cd apps/mobile-android
.gradlew.bat testDebugUnitTest assembleDebug
~~~

iOS requires macOS, Xcode and XcodeGen:

~~~bash
cd finalbuild/apps/mobile-ios
xcodegen generate
xcodebuild test -project AICarScanner.xcodeproj -scheme AICarScanner -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' CODE_SIGNING_ALLOWED=NO -enableCodeCoverage YES -resultBundlePath TestResults.xcresult
~~~

These are run instructions, not test results.

## F. Coverage

No measured coverage percentage is available for the current source or audit change. The configured 90% backend gate applies only to the selected diagnostic/telemetry/multi-ECU/simulator/global-data/AI reasoning/ML modules. It must not be presented as 90% whole-repository coverage.

Important unmeasured branches include API error paths, persistence failure/concurrency, missing/unseeded catalog states, process startup, packaged Windows smoke tests, mobile offline/network failure states, and cross-platform status/localization parity.

## G. API and database

- API routes are separated by session/intelligence, AI/RAG, decisions, telemetry, acquisition, vehicle diagnostic, multi-ECU/multi-bus, discovery, devices, vehicle catalog and global-data concerns.
- Android and iOS use the same primary session/analysis route pattern, but no fresh client/server contract test was executed.
- Vehicle catalog is PostgreSQL-backed and can return 503 if the database or seed rows are missing; /health is liveness-only.
- Session snapshot persistence coexists with a larger normalized schema; migrations/upgrade behavior were not exercised.
- The catalog has multiple overlapping schemas/seeds and needs a single source-of-truth pipeline.
- API authentication/tenant enforcement is not demonstrated at the route boundary.

## H. Platform report

### Desktop

A PySide6 client, API client, backend worker, optional local LLM process management, icon scripts and PyInstaller specs are present. The package-path and port-default defects listed above were corrected in source. A Windows build and launch remain unverified. Desktop UI localization is documented as incomplete. The missing-model/server and port conflict paths need persistent logs and visible UI status testing.

### Android

The application is native Kotlin/Jetpack Compose; Flutter was not found in the checked tree. API/repository/ViewModel/UI and BLE/Wi-Fi/USB foundations exist. Catalog fallback labeling, full session history, remote telemetry/simulator, discovery and AI-provider UI parity remain incomplete. local.properties was removed from source control because it contained a developer-specific Windows SDK path.

### iOS

The application is native SwiftUI with API models and XCTest contract/error-path files. Its README documents BLE discovery as a foundation only: complete connection/live OBD streaming is not implemented. Session history, telemetry/simulator, network discovery, report/export and AI-provider surfaces remain incomplete. The most recent checked-in note said the icon update had not yet been validated with XcodeGen/Xcode. No current build/test result is claimed.

## I. AI and diagnostic reasoning

The deterministic engine has explicit logic for the W211 E350 M272 petrol/LPG P0302 case. It should surface LPG delivery/mixture, ignition/combustion, air-fuel/intake and mechanical-cylinder hypotheses without declaring a coil definitively faulty. The rule engine includes LPG pressure measurement, petrol-vs-LPG fuel-trim comparison and injector-balance checks.

The regression contract has been strengthened but remains unexecuted. Evidence association is primarily rules and keyword/category matching, and the status score is heuristic rather than calibrated probability. Optional RAG/LLM assistance is not proof of diagnostic correctness and must not replace deterministic findings.

## J. Performance

No new latency values were collected. The existing harness applies a p95 budget below 90 ms to a deterministic intelligence-analysis call and times a deep-copy plus analysis operation. It does not prove end-to-end API p95, catalog/database scaling, RAG retrieval, LLM inference, UI frame rate or cold startup. Whole-session persistence may add a significant scaling cost and should be profiled separately.

## K. CI and release readiness

No workflow was triggered or rerun. The GitHub CI workflow is configured for pull requests and manual dispatch; the iOS workflow is manual-dispatch only. codemagic.yaml has no automatic triggering.events block. Do not interpret the absence of a run as a passing build.

Historical Actions information reviewed:
- Last successful project CI run observed on main was 2026-10-09 at commit 65fe581505d0c780557961b61a52853211cbd638, before the audited main commit.
- PR run 38399419273 on 2026-10-13 reported Android, Desktop and Python jobs failed in about two seconds, but job steps/logs were unavailable. Its root cause is undetermined; this report does not attribute it to code or payment.

Release is still blocked by lack of local tests and platform builds, API security enforcement, catalog unification, session persistence scaling/concurrency, metric semantics, offline UI clarity and verified package/runtime smoke tests.

## L. Ordered next actions

1. In PyCharm, run the Python suite and inspect the actual first failure(s); do not start cloud CI.
2. Run the tightened LPG golden test and the desktop custom-port/icon tests.
3. Build the desktop package on Windows using the updated script and launch it with backend online/offline, missing model/server, custom/busy ports and clean shutdown.
4. Wire API authentication/authorization and tenant/session isolation before public production use.
5. Refactor persistence to target sessions and add concurrency/scale tests.
6. Consolidate catalog schema/generators and contract-test every platform's online/offline data.
7. Use explicit unknown fields and defined units for confidence/ranking/cost metrics.
8. Expose stale/offline catalog, backend errors and deterministic-only mode visibly in Android/iOS/Desktop.
9. Run Android and iOS tests on their native toolchains.
10. Measure coverage and latency by clearly named scopes, then introduce reliable per-platform gates.

## M. Final repository state for this audit

- Branch: main.
- Base commit audited: 36dd6bddb946c56ca3dafe44d1bd6b11b9817f84.
- Change type: source fixes, regression tests, repository hygiene and report update.
- CI: not run.
- Project tests: not run.
- Coverage/performance: not measured.
- Windows/Android/iOS builds: not run.
- Generated executable, local SDK configuration and empty FETCH_HEAD: removed from the current tree; no history rewriting.
- Commit/push: changes are being recorded as one direct main-branch commit; runtime validation remains explicitly pending.
