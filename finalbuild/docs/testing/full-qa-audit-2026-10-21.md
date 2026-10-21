# Full QA audit — 2026-10-21

Audited baseline: `7ca8616`, with the fixes described below applied and retested.
This is a measured cloud audit, not certification of physical OBD hardware,
Windows packaging, or iOS simulator behavior. Counts are test executions per
suite; Desktop/main suites overlap and should not be summed as unique tests.

## Measured results

| Area | Result | Coverage / validation scope |
|---|---|---|
| Main Python suite | 541 passed, 1 skipped | `backend`, `vehicle`, `device`: **97.42% statements**, **87.52% branches**; combined statement/branch metric 95.57% |
| Desktop | 339 passed, all 5 groups exit successfully | **90.11%** complete Desktop source inventory; **91.06%** production-core statements; both existing 90% gates pass |
| Android JVM | 88 passed | JaCoCo: **33.39% lines**, **17.45% branches**, **19.78% instructions**; includes presentation code in denominator |
| Android native UI checks | 13 passed | Supplemental Robolectric/API-35 native-graphics harness; actual Compose rendering and interactions, not emulator/device tests |
| Android build/static analysis | Debug APK and androidTest Kotlin compilation pass | `lintDebug`: **0 errors, 21 warnings** |
| iOS | 10 Swift files parse without syntax errors | **28 XCTest cases declared but not executed**; Xcode compilation, runtime tests and coverage remain unverified |
| Python critical static checks | 0 findings | Ruff E9/F63/F7/F82; Python compileall passes |
| Python dependency audit | 64 installed distributions audited; 0 known vulnerabilities after update | `pip-audit` against the pinned installed environment; not a guarantee about future dependency resolution or bundled native libraries |

Final Python validation used Python 3.13.5, pytest 9.1.1 and Pillow 13.0.0.
Android used JDK 17, compile SDK 36, target SDK 35, AGP 8.13.0 and JaCoCo 0.8.13.
The skipped Python test requires a running PostgreSQL/pgvector service.

### Coverage breakdown

| Source scope | Statement/line coverage | Branch coverage |
|---|---:|---:|
| Backend Python | 97.75% | 88.71% |
| Vehicle/protocol Python | 96.43% | 85.56% |
| Device Python | 98.40% | 75.00% |
| Android OBD | 96.00% | See raw JaCoCo report |
| Android settings/translations | 99.56% | See raw JaCoCo report |
| Android repository | 80.00% | See raw JaCoCo report |
| Android API/models | 63.41% | See raw JaCoCo report |
| Android presentation | 10.20% | See raw JaCoCo report |

Desktop coverage above is statement coverage, not branch coverage. The complete
inventory retains probes, packaging hooks and smoke modules. No source was
excluded or coverage gate lowered to obtain a passing result.

The supplemental Robolectric checks exercise UI behavior, but the standard AGP
JVM coverage report does not capture their Compose execution reliably across
Robolectric class loaders. A run including those checks still reports 33.39%
line coverage. Do not claim complete UI coverage from their passing count.
Use connected/emulator instrumentation coverage for that measurement.

## Failures found and fixed

1. **Desktop widget teardown crashed after reporting 18 passes.** The original
   isolated widget process exited with SIGSEGV. Its fixture now closes and
   schedules destruction of top-level Qt widgets, drains deferred deletes and
   collects Python cycles before QApplication teardown. The complete Desktop
   matrix was rerun and all processes exit successfully.
2. **Desktop SQLite startup lacked failure-path regression coverage.** Added
   tests verifying catalog preparation precedes Uvicorn and a preparation error
   prevents server startup. Both success/error paths pass. The initial Desktop
   complete-source coverage was 89.98%; final measured coverage is 90.11%.
3. **Android lint rejected Bluetooth permission handling.** RFCOMM connection now
   explicitly returns a failure on revoked permission and closes pending/stored
   sockets. Cancellation propagates and cleans up instead of becoming an ordinary
   connection failure. Added permission-revocation and cancellation tests.
4. **Android UI test constructed a ViewModel inside composition.** Construct it
   once before `setContent` so recomposition cannot recreate it. No lint errors
   were suppressed or baselined.
5. **iOS dismissed result entry even on API failure.** Failed submissions now
   retain the sheet and notes, show the error and permit retry. Pending requests
   disable editing/submission/dismissal; success returns to Analysis with the
   recalculated server session. Swift syntax validation passed; runtime validation
   still requires Xcode.
6. **Known vulnerable Python dependencies were installed.** Pillow 12.3.0 and
   pytest 8.4.2 were flagged by the advisory service. Requirements now require
   Pillow `>=13,<14` and pytest `>=9.0.3,<10`. Installed Pillow 13.0.0/pytest 9.1.1,
   reran main and Desktop suites, and repeated the dependency audit: no known
   vulnerabilities found in the 64-distribution inventory.
7. Added a permanent Android instrumented regression for translated diagrams,
   score updates and latest-result counting, plus iOS XCTest assertions for the
   selected-language outcome labels. Android instrumentation compiles; the iOS
   assertions are committed but not executed in this Linux environment.

## Real-process and performance checks

`python scripts/check_local_backend.py` passed using isolated temporary SQLite
storage and an actual Uvicorn child process:

- Startup healthy in **2.16 seconds**.
- **369** catalog entries with valid fuel arrays.
- Session creation, symptom and P0302 entry, hypotheses and recommended tests.
- Backend restart preserves session, DTC, hypotheses and catalog row count.

The deterministic diagnostic benchmark runs 100 measured cases after warmup:
**p50 0.68 ms**, **p95 2.32 ms**, maximum 20.63 ms; the existing p95 budget is
90 ms. This measures deterministic in-process reasoning, not LLM latency, network
round trips, physical adapters or production diagnostic accuracy.

## Remaining work, in priority order

1. **iOS native verification:** run the manual Native iOS Tests workflow or local
   Xcode XCTest with coverage. This cloud has no macOS/Xcode, and an authenticated
   GitHub workflow session was unavailable. Swift parsing is not type checking;
   current charts, API failure UI and 28 tests need native execution.
2. **Android UI coverage:** run the committed androidTest suite on an emulator
   and aggregate instrumentation coverage. Add more complete session/edit/history,
   result-failure/retry and adapter-permission flows. The 33.39% JVM line metric
   is an outstanding coverage gap, not a release-grade whole-app percentage.
3. **Platform/device checks:** Windows packaged EXE startup/icon/shutdown and
   actual Bluetooth/Wi-Fi/USB hardware on supported devices were not exercised.
   iOS currently implements BLE discovery, not full OBD connection/streaming.
4. **Database/provider integration:** bring up PostgreSQL/pgvector to remove the
   skipped integration test, and validate a configured real LLM provider. Current
   golden-case/contract tests and mocks do not establish production AI accuracy.
5. **Android lint warnings:** 21 remain, covering dependency/target-SDK updates,
   icon/resource duplication/location and optional KTX cleanup. They were
   retained rather than hidden. Review upgrades individually with compatibility
   tests; the current audit did not change Android target SDK or libraries.
6. **Python branch gaps:** device branches are 75%, vehicle 85.56%; add meaningful
   transport timeout/cancellation/recovery tests. Desktop UI is 88.49% statements
   even though the aggregate gates pass.

## Reproduce

From `finalbuild/`, after installing runtime/dev requirements:

```bash
python -m pip install -r backend/requirements-dev.txt -r apps/desktop/requirements-dev.txt
QT_QPA_PLATFORM=offscreen AI_CAR_DISABLE_LLM_AUTOSTART=1 AI_CAR_USE_LOCAL_DATABASE=1 \
  python -m pytest tests -q --cov=backend --cov=vehicle --cov=device --cov-branch \
  --cov-report=term-missing --cov-report=xml --cov-report=html
python scripts/run_desktop_tests.py --min-coverage 90 --min-core-coverage 90
python scripts/check_local_backend.py
python -m pytest -q -s tests/harness/test_performance.py
```

From `finalbuild/apps/mobile-android/` with JDK 17 and the Android SDK:

```bash
./gradlew :app:testDebugUnitTest :app:createDebugUnitTestCoverageReport :app:lintDebug \
  :app:compileDebugAndroidTestKotlin :app:assembleDebug
# Requires an actual emulator/device; not executed by this cloud audit:
./gradlew :app:connectedDebugAndroidTest :app:createDebugAndroidTestCoverageReport
```

From `finalbuild/apps/mobile-ios/` on macOS with Xcode/XcodeGen:

```bash
xcodegen generate
xcodebuild test -project AICarScanner.xcodeproj -scheme AICarScanner \
  -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' \
  CODE_SIGNING_ALLOWED=NO -enableCodeCoverage YES -resultBundlePath TestResults.xcresult
xcrun xccov view --report TestResults.xcresult
```

## Evidence artifacts

Raw generated reports are deliberately not committed. In the audit workspace:

- `/workspace/qa-review/summary.json`
- `/workspace/qa-review/python-coverage.json`, `python-coverage.xml`, `python-html/`
- `/workspace/qa-review/python-junit.xml`, `python-tests-final.log`
- `finalbuild/desktop-test-reports/summary.json`, `coverage.json`, `htmlcov/`, group logs/JUnit
- `/workspace/qa-review/android-unit/`: unit JUnit, JaCoCo HTML/XML and lint HTML/XML
- `/workspace/qa-review/android-with-ui/`: supplemental 101-case run and reports
- `/workspace/qa-review/backend-startup.log`, `performance.log`
- `/workspace/qa-review/python-dependency-audit-final.json`
- `/workspace/qa-review/ios-static.json`

The native-graphics harness is supplemental cloud tooling outside the repository;
its passing result is not a substitute for the committed connected androidTest suite.
