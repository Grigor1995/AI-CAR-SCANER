# Release notes

## Unreleased — Android/Desktop catalog and display alignment

- Package the same backend-generated offline snapshot on Desktop and Android,
  with 20 makes and 72 generation identifiers; backend rows retain priority.
- Include all snapshot generation portraits in native mobile bundles.
- Add Android analog/line widgets and EU/USA display units, matching Desktop
  channel names and current-plan test progress. Handle unknown ECUs safely.
- Review and limitations: docs/reviews/android-desktop-parity-2026-10-23.md.
- Local tests/builds only; CI/CD is skipped.

## Unreleased — Android test APK build

- Updated the instrumented UI test API fixture for backend vehicle registry,
  protocol compatibility and photo metadata endpoints, restoring test APK
  compilation. Fixtures do not claim real hardware compatibility.
- Android debug APK and local JVM/lint validation use the emulator backend URL
  http://10.0.2.2:8001/. CI/CD is skipped.

## Unreleased — Restore the dashboard before layout sliders

- Restored the dashboard layout from before resizable/movable widget controls.
- Retained analog gauges, readable parameter names, USB OBD fixes and responsive
  shutdown. Saved slider-layout preferences are no longer used.
- Validated locally; CI/CD is skipped.

## Unreleased — Responsive Desktop shutdown

- Cancel outstanding API response waits when closing, including long-running AI
  requests. Qt workers finish safely without waiting for HTTP read timeouts.
- Late responses and errors cannot update a closing window. Already-sent server
  operations are not rolled back; socket I/O ends on daemon transport threads.
- Regression tests cover a blocked session-creation request and prompt window
  closure without destroying a running QThread.

## Unreleased — Named widgets and analog dashboard gauges

- Fixed newly added telemetry widgets retaining raw PID titles or empty channel
  selectors; backend names take precedence, with an offline backend-registry
  snapshot for older acquisition responses. Stable channel IDs remain unchanged.
- Added analog dials alongside selectable line charts, with numeric readouts and
  saved per-widget display modes. RPM, temperature and speed use unit-aware
  display scales; scales are visual ranges, not diagnostic limits.
- Kept the vehicle-list stale-index regression protection from the preceding fix.

## Unreleased — Real USB OBD connection selection

- Keep USB serial names (COM3, COM4, /dev/ttyUSB0) separate from numeric Wi-Fi
  ports, and send the selected serial name to the backend when connecting.
- Ignore stale vehicle selection indices and suppress selection callbacks while
  rebuilding the vehicle list.

## Unreleased — Live simulator controls and measurement units

- Added live RPM, coolant temperature, speed and throttle controls, validated by
  the backend; physical adapter measurements cannot be edited. Apply changes
  after starting the simulator without clearing previous samples.
- Added persistent EU (km/h, °C) and USA (mph, °F) display settings. Diagnostic
  evidence remains in canonical SI units.
- Made Live Data scrollable, centered constant traces, and stabilized channel
  selections when the acquisition record window rotates.
- Current test progress counts only the displayed recommendation plan; an empty
  plan shows 0/0 even when historical results exist.

## Unreleased — Guided tests and Live Data parameter names

- Retained rule-specific recommendations in executable decision plans and
  refreshed the Desktop test list after live-data AI analysis. Added an explicit
  generate-tests action and guidance when evidence is missing.
- Kept INCOMPLETE tests available; PASS/FAIL outcomes remain completed.
- Removed the duplicate visible result selector/submit row; the three outcome
  buttons record results with the technician notes.
- Added backend-owned parameter display names while preserving stable wire IDs
  and saved widget selections. Desktop titles/dropdowns use readable localized
  labels instead of raw PID hex numbers.
- Verified 812 Python tests (2 skipped) and 404 Desktop tests (1 skipped).

## Unreleased — Managed offline AI startup

- Added Desktop `--local-ai` to override an earlier external OpenAI-compatible
  selection and start a local GGUF runtime with the managed backend.
- Fixed source-mode llama-server discovery, single-GGUF model selection and
  custom local endpoint port/`/v1` normalization.
- Added `python scripts/check_offline_ai.py` to inspect required files and the
  actual runtime/backend provider, including stale external-provider instances.
- Verified 810 Python tests (2 skipped) and 400 Desktop tests (1 skipped);
  Desktop source/core coverage was 90.53% / 91.51%. These checks do not claim
  real model inference: the model weights are on the user machine.
- See [offline AI setup](finalbuild/docs/ai/OFFLINE_AI.md).

## Unreleased — Generation portraits and advanced read protocols

- Fixed Desktop portrait loading on supported PySide6 versions by passing
  string header names to `QNetworkReply.rawHeader`. Added a real Qt/loopback
  HTTP regression test for image loading and UTF-8 attribution.

- Expanded shared selection from 50 to 70 generations and 199 engine options.
- Added 51 generated transparent portraits; all 70 generation references now
  have distinct images served by the backend.
- Added explicitly addressed ELM/CAN UDS reads, DoIP TCP routing/UDS reads,
  passive J1939 DM1/DM2 with TP.BAM reassembly and J1708/J1587 packet decoding.
- Corrected confirmed-DTC interpretation to ISO 14229 status bit 3.
- Verified 802 Python tests (2 skipped), 387 Desktop tests (1 skipped), 70/70
  transparent generation portraits and the Android build/unit tests.
- Preserved read-only operations and explicit capability limits. OEM drivers,
  CAN FD and regulatory WWH-OBD/OBDonUDS profiles are not universally implemented.
- See [scope, endpoints and validation](finalbuild/docs/obd/EXPANDED_CATALOG_AND_PROTOCOLS.md).

## Unreleased — Shared OBD backend and vehicle references

### Feature branch integration

- Merged `feature/backend-unified-vehicle-obd-audit-20261022`, retaining its
  global registry, engine/protocol profiles, NHTSA lookup adapters and source
  metadata alongside shared backend decoding/native transport bridges.
- Resolved the backend packaging and device protocol endpoint conflicts. The
  packaged backend includes both catalogs and images; protocol observation
  accepts both backend manager implementations and never labels a simulator
  as physical ECU evidence.
- Preserved explicit `backend.vehicle` simulator imports while routing the
  unqualified `vehicle` name to the canonical shared implementation.
- Verified 739 Python tests (2 skipped), 387 Desktop tests (1 skipped), actual
  FastAPI source startup and Android build/tests. Desktop source/core coverage
  was 90.42% / 91.39%. iOS syntax was checked; Xcode was unavailable.


- Centralized ELM initialization, ten live-data PID formulas, protocol selection,
  telemetry ingestion and vehicle references in the backend. Android and iOS
  native bridges forward adapter bytes; Desktop can start a connected adapter.
- Connected the public backend device API to server-local USB serial, BLE GATT
  and Wi-Fi transports. Added strict ELM/ISO-TP reply parsing, bounded timeouts,
  stored/pending/permanent DTC reads and supported-PID discovery.
- Added 50 generation references / 147 engine options with fuel types, source
  links and explicit unverified-fitment labels. Protocol candidates require
  adapter detection; this is not a claim of universal vehicle compatibility.
- Added backend image delivery and an attributed Commons photo importer. Actual
  photo downloads were blocked by HTTP 403 here; existing illustrations remain.
- Added Android build-time backend URL selection with `--android-api-url`.
- See the [OBD audit and validation boundaries](finalbuild/docs/obd/REAL_OBD_AUDIT.md)
  and [deployment/API guide](finalbuild/docs/obd/SETUP_AND_API.md). DoIP, CAN FD,
  enhanced OEM diagnostics and physical UDS API support remain unimplemented.
  iOS requires Xcode/device verification; no physical vehicle was tested.

## 0.6.0 — Native UI, build and reliability update

**Date:** 2026-10-22  
**Source revision:** [`82cc013`](https://github.com/Grigor1995/AI-CAR-SCANER/commit/82cc013)  
**Platforms:** Desktop, Android and iOS

These notes cover the integrated native-client changes, unified builder and
repository cleanup through this source revision. The existing version remains
0.6.0; these notes do not create a release tag or publish application binaries.

### Added

- Updated native dashboards and transparent, model-specific vehicle portraits.
- Diagnostic analysis workspaces with test results and analysis diagrams on
  Android and iOS. Recording a test outcome updates the diagnosis through the
  backend's recalculation flow.
- Vehicle editing, language/theme controls, and localization improvements for
  English, Armenian and Russian, including diagnostic test outcomes.
- A shared `python build.py` entrypoint with prerequisite checks, optional
  tests, per-run logs, artifact checksums and a build summary.
- A three-platform GitHub Actions build workflow using Windows, Android and
  macOS runners.
- A [demo presentation and supporting evidence](finalbuild/docs/demo/README.md).

### Fixed

- Local backend startup/storage configuration and bounded FastAPI crash
  recovery, with separate backend, acquisition and AI availability states.
- OpenAI-compatible runtime readiness and configuration for tools such as
  LM Studio; externally managed providers do not spawn a competing llama-server.
- Vehicle selection artwork refresh and unnecessary model/brand controls.
- Session IDs are hidden from user-facing session displays and exported
  diagnostic reports while remaining available for internal routing/storage.
- Desktop tests that incorrectly inherited the user's LLM URL/provider.
- PDF export now specifies a printable font size and black text. Its behavior
  still requires confirmation on native Windows.
- Long builds now display live output. Ctrl+C stops the owned command tree,
  records `CANCELLED`/`NOT_RUN` statuses and exits with code 130.
- Desktop test reports are retained inside each build's artifact directory.
- CI coverage targets now include `global_data` and `ai.live_analysis` correctly;
  Qt widget tests are required rather than tolerated failures.

### Cleanup

- Removed the web/PWA and legacy Flutter client scaffolding; supported clients
  are native Desktop, Android and iOS.
- Removed unused mobile SVG illustrations, duplicate Android icons,
  disconnected placeholder code, unused imports and dependencies.
- Removed one byte-identical test file while retaining its unique assertions.
- Preserved PNG portraits, active offline catalogs, database schema models,
  hardware integration interfaces and the requested demo/report evidence.
- Added a [full audit and file/declaration inventory](finalbuild/docs/maintenance/full-repository-audit-2026-10-22.md).

### Verification

Results below apply to source revision `82cc013` on the Linux validation host.
Root Python and Desktop suites overlap; their counts are not additive.

| Check | Result |
|---|---|
| Python suite in a clean dependency environment | 589 passed, 2 skipped |
| Backend/core coverage | 95.89% (minimum 90%) |
| Desktop regression matrix | 384 passed, 1 skipped |
| Desktop production core coverage | 91.17% |
| Actual source FastAPI subprocess startup | PASS |
| Android JVM tests | 89 passed |
| Android debug APK, app/instrumentation compilation and lint | PASS |
| Android lint findings | 12 warnings, 0 errors, 0 unused-resource findings |
| Swift syntax parsing | 10 files PASS |
| Python static checks, internal import graph and structured-file syntax | PASS |

Native Windows EXE packaging, PowerShell execution, native Xcode typechecking/
XCTest, emulator instrumentation execution and physical OBD hardware were not
validated on this host. Swift parsing is not an iOS build or test result.

### Update and build

From the repository root:

```bash
git pull origin main
python build.py --check
```

On Windows with the Desktop and Android prerequisites installed:

```bash
python build.py --targets desktop android --with-tests
```

For all three platforms, use **Actions → Build all native apps → Run workflow**,
or an authenticated GitHub CLI:

```bash
python build.py --ci --with-tests
```

Outputs are a Windows application ZIP, Android debug APK and unsigned iOS
Simulator app ZIP. Device/App Store distribution requires Apple signing; the
Simulator ZIP is not an installable iPhone IPA. AI model/server binaries remain
separate setup requirements.

See [build instructions](finalbuild/docs/building/BUILD_ALL.md) for toolchains,
artifact locations, result codes and platform constraints.
