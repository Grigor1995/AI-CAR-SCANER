# Android Code Audit & Local-Only Coverage Plan

Date: 2026-10-16  
Repository scope: `finalbuild/apps/mobile-android`  
Status: **static review complete for the main Android sources; new tests awaiting local execution**  
Working branch: `test/android-coverage-local-20261016`  
CI policy: **no workflow dispatch, no PR before local validation**.

## Baseline: distinguish test execution from coverage

- Latest confirmed Android instrumented test run: **13 passed, 0 failed, 0 skipped** on `Pixel_6_Pro(AVD) - 17`.
- User-supplied `debug` report: **62% instruction coverage** (10,488 missed of 28,334); **26% branch coverage** (1,074 missed of 1,455); approximately **63.7% line coverage** (710 missed of 2,238). The table appears to be from the Android instrumentation report but report provenance has **not** been independently confirmed.
- By package, reported instruction coverage: presentation 70%, OBD 3%, settings 68%, API 70%, repository 85%, application entrypoint 0%.
- Existing JVM OBD unit tests are present. Their execution coverage cannot be inferred from the instrumentation table. Avoid interpreting OBD's 3% as combined unit+instrumentation coverage.
- **90% remains a target, not a measured result.** No new coverage percentage is claimed from the additions below.

## Architecture inventory

| Layer | Main implementation | Main responsibilities |
| --- | --- | --- |
| Android entry | `MainActivity.kt` | ViewModel/Repository creation and Compose host |
| Compose UI | `presentation/DiagnosticScreen.kt` | Vehicle selection, symptoms, DTCs, session, OBD transport, live telemetry, analysis, settings, test results |
| UI state | `presentation/DiagnosticViewModel.kt` | Session orchestration, coroutine dispatch, API failures |
| ViewModel creation | `presentation/DiagnosticViewModelFactory.kt` | Repository injection |
| Vehicle catalog | `presentation/VehicleCatalog.kt` | Local fallback and remote selection filters |
| Networking | `data/api/{ApiClient,DiagnosticApi}.kt` | Retrofit client, DTOs, request contract |
| Repository | `data/repository/DiagnosticRepository.kt` | Backend operation delegation |
| OBD hardware | `data/obd/{BluetoothObdClient,WifiObdClient,UsbObdClient}.kt` | Transport connection, ELM327 setup, commands |
| OBD parsing | `data/obd/LiveDataReader.kt` | Read and scale live PID values |
| Settings / localization | `settings/{AppSettings,Strings}.kt` | Preferences and English/Russian/Armenian strings |
| Android settings | `AndroidManifest.xml` | Permissions, USB feature, application configuration |

## Static findings to verify

### High priority

1. **OBD readiness may be incorrectly reported.** Each OBD client calls `initialize()`, but the initializer does not check whether its `command("AT...")` calls succeeded. A transport connection could be considered successful despite adapter initialization failures. Add a failure-contract test and make initialization results explicit before changing user-visible behavior.
2. **Timeout is not necessarily a failure.** Commands in the Wi-Fi/Bluetooth/USB clients return a successful `Result<String>` containing a partial or empty response when the prompt `>` is not received before the deadline. Confirm the intended contract, distinguish complete from partial frames, and test timeout semantics. A characterization test was added for the current Wi-Fi behavior.
3. **Stale async session responses.** `DiagnosticViewModel.execute()` starts independent coroutines; a slower earlier action may publish after a newer action or after `clearSession()`. Add reproducible tests for out-of-order completion and reset during a pending request before choosing a cancellation, version-token, or serialization strategy.
4. **Large UI unit.** `DiagnosticScreen.kt` is about 1,712 lines long and owns transport clients, lifecycle I/O, form logic, session presentation and dialogs. Split stateful logic into testable controllers/composables in small behavior-preserving increments; do not refactor everything during one coverage pass.

### Medium priority

5. **Restricted network configuration.** The manifest sets `android:usesCleartextTraffic="true"` globally. Review whether local adapter TCP and optional local backend require cleartext HTTP and restrict that exception if possible.
6. **Persistent settings and runtime permission behavior.** Preferences and language/theming have some tests, but runtime permission denied/granted, app restoration, and Bluetooth/USB device discovery need instrumentation on representative Android versions/devices.
7. **Hardcoded backend URL.** `ApiClient.kt` targets `https://ai-car-scaner.onrender.com/`. Prefer configurable backend environments when adding staging/mock integration test workflows.
8. **Result and localization contracts.** Keep `PASS`, `FAIL`, `INCOMPLETE` for API payloads and assert translated labels and server-selected language independently. Do not change API enum values based on UI translation.

## Test additions in this branch (not executed here)

- `BluetoothObdClientConnectTest.kt`: successful RFCOMM initialization, command write order, RPM and DTC responses, sanitization, socket cleanup.
- `UsbObdClientConnectTest.kt`: successful USB bulk-interface claim and device initialization, RPM/DTC reads, interface release and cleanup.
- `WifiObdClientTest.kt`: incomplete-frame/timeout characterization and subsequent valid command response.
- `DiagnosticViewModelTest.kt`: pending request loading lifecycle and no-session guards for remaining actions.
- `DiagnosticScreenInstrumentedTest.kt`: empty Analysis/Activity states, Russian language + light theme switching, vehicle edit cancellation.

The full instrumented test count is expected to grow from **13 to 16** after the new UI tests are compiled and run. This is a *planned count*, not a test execution result.

## Exact local validation

From `finalbuild/apps/mobile-android` after checking out the branch:

```bash
./gradlew testDebugUnitTest --rerun-tasks
./gradlew createDebugUnitTestCoverageReport
./gradlew connectedDebugAndroidTest --rerun-tasks
./gradlew createDebugAndroidTestCoverageReport
```

Compare the reports **separately**:

- JVM unit test coverage: `app/build/reports/coverage/test/debug/index.html`.
- Android instrumentation coverage: `app/build/reports/coverage/androidTest/debug/connected/index.html` (verify actual path with a local file search if AGP emits a variant location).

Record test totals, exact coverage table, branch and commit, test device/API level, failing XML details, and any warnings. If all local checks pass, verify branch and PR trigger implications before merging. `ci.yml` triggers on `pull_request` touching `finalbuild/**`; `ios.yml` is `workflow_dispatch` only. Branch commits do not independently match those triggers, but opening a PR **would** start CI.

## Criteria for sign-off

1. Unit test run passes locally.
2. All instrumentation tests pass locally on the Pixel AVD.
3. Both coverage reports are supplied and improvements attributed to their respective suites.
4. No tests weakened, no production sources excluded solely to inflate percentage, and no regression in user-facing diagnostic behavior.
5. Merge only after the preceding conditions have been checked and an explicit no-CI merge path has been confirmed.
