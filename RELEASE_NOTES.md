# Release notes

## Unreleased — First-clone runner bootstrap fix (2026-10-29)

- Fix `ModuleNotFoundError: backend` when starting runner.py from the repository root.
- Keep setup/help/check dependency-free before the project venv exists; share stdlib JSON/version loading, then validate the full global configuration inside the installed venv and on every backend startup.
- Add clean `python -S` subprocess coverage and namespace/bridge parity checks. Existing ENV precedence, AI model discovery and backend validation remain intact.

## Unreleased — Optional catalog microservice, global config and source explorer (2026-10-29)

- Add a real independently executable read-only vehicle catalog with authenticated internal HTTP, bounded retries/timeouts, no redirect credential forwarding, and an account-protected gateway. Embedded mode remains the default; private diagnostics/business SQL remain on the shared backend.
- Add strict versioned global JSON/schema and environment overlays, frozen snapshots, legacy ENV compatibility and audited ADMIN-only runtime timeout/retry changes. Purchase/payment flags remain disabled; policy-only fields are identified in the config reference.
- Extend the existing offline architecture explorer with a generated Python AST/native syntax index, 12 source views, symbol previews/call evidence, node/group dragging and saved/exportable layouts. Dynamic/native semantic gaps remain explicitly unresolved.
- Add distinct generated USER, CUSTOMER and MARKET icons for Desktop, Android flavors, iOS targets and installer shortcuts. Preserve other application artwork and UI.
- Verify 1133 common tests (2 skipped), all five Desktop groups with 90.36% production core coverage, Android three-flavor build/tests/lint, browser interaction tests and two-process gateway failure/rollback smoke. Windows installer, iOS runtime, Docker execution and physical OBD acceptance remain unverified here.

## Unreleased — Three independent apps and centralized backend

- Centralize real vehicle/protocol code, server/AI lifecycle and PDF rendering under finalbuild/backend; retain small compatibility exports and preserve legacy behavior.
- Package USER, CUSTOMER and MARKET separately on Desktop/Android/iOS with fixed workspaces, separate application identities/settings and one shared backend. ADMIN remains API-only.
- Add explicit backend startup/migration command, independent client launch/build selection, business onboarding and app-owned backend URL configuration.
- Windows artifacts separate three GUI clients from one headless backend; Android produces three APKs; Xcode defines three bundle targets. Update source installer to three shortcuts.
- Full business native editors and unavailable providers remain partial/blocked. See docs/business/THREE_APP_DEPLOYMENT.md for executed verification and platform limits.

## Unreleased — Incremental business workflows (2026-10-29)

- Add owner/consent-scoped persistent diagnostics using the existing engine, explicit staff acceptance, work orders, verified directory and curated reference registry.
- Add moderated merchant products/inventory and server-side public/professional/center/coupon/quantity quotes. MARKET remains a portal; payments are inactive and compatibility is an unverified seller claim.
- Add audited admin governance, durable deferred/missed monitoring lifecycle and in-app notices, account preferences, engineering conversions and localized diagnostic response copies.
- Add native account registration/login/read workspaces while preserving current UI/icons. Complete business mutation UI, unattended gateway scans, external verification/delivery, licensed sources and full French parity remain incomplete.
- Add additive migration 0002, 25 business documents, interactive dashboard and executed QA evidence. Common suite: 1091 passed, 2 skipped; ecosystem coverage 98.06%; Desktop groups and Android build/lint pass. iOS/Windows hardware/provider limitations are explicit.

## Unreleased — Measured telemetry optimization (2026-10-29)

- Reuse sorted/filtered signal samples for telemetry statistics and events while preserving public APIs, arithmetic and current UI/assets.
- Paired synthetic 1k/10k/50k summary benchmarks show about 11–20% lower p50 on the audit host; hardware/LLM latency is not inferred.
- Add exact regression cases, reproducible profiling scripts, optional C++20 experiment and an interactive local performance dashboard. Keep C++ outside production because simpler Python alternatives beat its copy-inclusive experiment.
- Full common suite: 1062 passed, 2 skipped; all five Desktop groups pass. Detailed platform limitations and raw evidence: docs/performance/FINAL_PERFORMANCE_REPORT.md.

## Development — Ecosystem foundation (new branch)

- Audit the existing platform and preserve its native UIs, shared DiagnosticSession, reasoning and transport modules; add local interactive architecture and staged implementation documentation.
- Add feature-gated v2 accounts, hashed/revocable bearer sessions, primary-mode authorization, owned legacy-compatible profiles and durable owner-approved workshop sharing.
- Add explicit Alembic migrations, scoped audit events and EN/HY/RU error responses. Invites grant no access until the owner accepts; revocation and expiry are rechecked on reads.
- With ecosystem mode enabled, block legacy anonymous API bypasses and skip anonymous global-session cache persistence. With it disabled, existing diagnostic clients retain their API behavior.
- Change runner bind default to loopback; trusted physical-LAN development requires an explicit host override. Native authenticated diagnostics/workspaces and remaining ecosystem phases are not yet production-ready.

## Unreleased — Installer source 404 recovery

- Bundle a SHA-256-verified snapshot of tracked source by default, so private GitHub repositories do not fail with unauthenticated source-download 404s. Keep `--online-only` for publicly downloadable commits.
- Exclude Git history and untracked/ignored local secrets from the source archive. Validate checksum and safe extraction before promoting source files.
- Display the actual setup failure in the wizard, persist early PowerShell transcripts/errors, and explain inaccessible-source HTTP errors. Keep AI/model/dependency downloads separate from the bundled source.

## Unreleased — Desktop-styled installer and shared configuration

- Style the Windows wizard with the Desktop navy/neon-blue palette and existing abstract vehicle artwork; add a dedicated AI model page and review summary.
- Choose AI weight download or a local GGUF checkbox/path/browser. Validate local files before setup, preserve external model files and remember the local choice on repair.
- Add shared versioned JSON ENV configuration for runner, Desktop and backend, with process/local overrides and packaged defaults. Installer shortcuts load the generated installation-level environment.json.
- Respect configured AI endpoints and effective ports in runner launch/health/emulator routing. Retain custom JSON values during upgrades.

## Unreleased — Windows online installer

- Add a local Inno Setup builder (`python installer.py`) producing Setup.exe and a SHA-256 checksum, with a pinned GitHub source snapshot.
- Install Desktop and Backend with optional local AI and Desktop shortcut checkboxes; provision signed official Python when missing and reuse the existing setup runner.
- Add Start menu launch/uninstall entries, hidden-console launch with logs, safe retries/upgrades and Windows Apps uninstallation. Preserve user diagnostic data and shared Python on removal.
- Keep installer compilation and Windows shell integration explicitly subject to a Windows smoke test; no CI/CD added.

## Unreleased — Windows Desktop PDF and build reliability

- Export offline Desktop PDFs with the same ReportLab renderer as backend reports, avoiding Windows Qt printer/COM failures and blank PDFs. Bundle the Unicode font for Armenian and Russian text.
- Read the dashboard translation test source explicitly as UTF-8 and run Desktop test subprocesses in UTF-8 mode on Windows.
- Keep the diagnostic-content and internal-session-ID checks, and verify offline PDF export in English, Armenian and Russian without OS printer access.

## Unreleased — Editable main menu order

- Reorder Desktop, Android and iOS launcher tiles by dragging; preserve the chosen order locally after reopening the app. Keep workflow destinations stable regardless of visual position.
- Desktop supports Ctrl+Left/Right; Android supports long-press drag with edge scrolling; native mobile accessibility exposes earlier/later actions. No move buttons or sliders are added.
- Recover safely from obsolete/duplicate saved entries and append new sections without losing menu items.

## Unreleased — Poll only observed supported live PIDs

- Add backend POST /api/v1/obd/plan to select implemented Mode 01 channels from complete ECU capability bitmaps, merging multiple responder masks without model-based assumptions.
- Cache live command selection per connection, refresh after reconnect or native session changes, and fail clearly on invalid or empty capability plans.
- Integrate the shared selector with server-local/Desktop adapters, Android native transport and iOS Wi-Fi; keep native clients free of bitmap decoding and scaling rules.
- Advertise explicit simulator capabilities and retain the legacy GET plan for older consumers. Backend and native apps should be updated together.

## Unreleased — OBD live acquisition reliability

- Show the observed protocol beside VIN discovery on Desktop/Android, requiring a positive ECU response rather than guessing from a selected model.

- Android: abort a native live poll on transport failure or cancellation instead of turning it into NO DATA and sending a misleading snapshot to the backend. Preserve successful NO DATA replies for unsupported PIDs.
- Bind polling to the selected transport/session, clear failed local readings and stop the loop when the adapter disconnects.
- Backend: propagate disconnected OBD reads to the acquisition reconnect manager, and cancel blocked reads promptly when Stop is requested.
- Keep completed rule-generated tests out of normal reanalysis; match by stable test names despite regenerated UUIDs.

## Unreleased — Android result submission

- Remove a silent click guard that ignored Record result while another request was loading. Opening the result editor no longer depends on unrelated requests.
- Track test submission and errors independently, prevent duplicate taps, surface failed saves in the dialog, and unlock retries after a timeout. Ignore older analysis responses that would replace a newly recorded diagnosis.

## Unreleased — Recalculate hypotheses after every test

- Rebuild evidence scores and hypothesis ranking from the latest outcome of each test on every analysis. PASS weakens targeted fault hypotheses, FAIL supports them, and INCOMPLETE withdraws the previous result for that test without inventing evidence.
- Persist test targets, replay earlier results after reopening a session, and replace corrected outcomes without double-counting repeated submissions or refreshes. Refresh remaining-test priorities from the resulting hypothesis statuses.
- Expose a numeric confidence_score independently of translated status labels; Desktop, Android and iOS use it for scores and diagrams. Scores remain heuristic evidence rankings, not calibrated failure probabilities.

## Unreleased — Mobile icon and consistent neon portraits

- Replace Android density/adaptive launcher icons and the iOS app icon with generated neon-blue abstract vehicle artwork. Android themed icons use a separate monochrome silhouette.
- Prefer the exact bundled generation portrait on Android/iOS so older backend artwork cannot replace the Desktop-matching neon image. Use remote artwork only when a generation has no bundled portrait.
- Keep all 72 model-generation images byte-identical across Desktop, Android and iOS.

## Unreleased — Native mobile neon presentation

- Reuse Desktop 3D icons, abstract vehicle branding, and background on Android and iOS.
- Add responsive launcher tiles, dimensional section headers and gradient cards.
- Hide workflow navigation on the launcher; retain home navigation on other pages.
- Move preferences into the application overflow menu and retain language/theme controls.
- Add a recessed bezel to Android live gauges without changing readings or reference bands.
- Android: local debug APK, JVM and lint checks. iOS requires Xcode validation on macOS; no CI/CD used.

## Unreleased — Compact neon-blue Desktop presentation

- Remove Settings toolbar buttons; preferences remain available from the
  Application menu. Give top navigation a full-width compact row with wrapped
  labels, and fit all sidebar links to the available height without navigation
  scrollbars in the supported 800×600 and larger test layouts. Reduce menu,
  sidebar and section-header icon sizes.
- Replace the menu car and background with generated abstract neon-blue vehicles,
  without a real manufacturer model. Individually regenerate all 72 catalog
  generation portraits in neon-blue 3D style, record their provenance and hashes,
  and synchronize the exact files into Android/iOS bundles. Preserve exact model
  selection and transparency; do not use a runtime color filter.
- Wrap Live Data actions, simulator inputs and narrow signal grids instead of
  introducing horizontal scrolling.
- Add illuminated depth to analog gauges and line charts. Preserve measurements,
  scales and reference bands; no simulated depth changes the plotted values.
- Local Desktop checks; CI/CD skipped.

## Unreleased — Responsive 3D Desktop workspace

- Fit all twelve launch tiles to the available window by adapting columns, image
  size and wrapped labels. Remove the fixed tile dimensions that forced menu
  scrolling; no size sliders or extra controls are introduced.
- Use the 3D artwork for all workflow headers, sidebar entries and top navigation.
  Apply matching beveled/gradient surfaces to section banners, cards and buttons
  in both themes. Reuse cached icons; keep existing diagnostic and telemetry flows.
- Verify the launcher at 800×600, 960×720, 1380×780 and 1920×1080 without menu
  scrollbars. Desktop-only presentation update; CI/CD skipped.

## Unreleased — 3D Automotive menu icons

- Replace the twelve primary Desktop launcher symbols with generated transparent
  3D automotive images: distinct OBD socket and VCI adapter, vehicle, gauges,
  inspection sheets, AI brain and ECU network. Keep native localized labels and
  the existing automotive background. Package the local sprite atlas in releases;
  retain SVG fallbacks. CI/CD skipped.

## Unreleased — Focused Desktop launch artwork

- Hide sidebar navigation and top section buttons on Main menu; restore them
  when entering a workflow. Keep branding visible.
- Add a generated dark automotive background and twelve distinct neon SVG menu
  images. Cache background scaling, preserve aspect ratio, maintain readable
  labels in both themes, and bundle the artwork in Desktop releases.
- Desktop-only presentation update. Local checks; CI/CD skipped.

## Unreleased — Large launch menu

- Open Desktop and Android on a large icon tile menu, with direct navigation to
  Symptoms, Diagnostics, VCI and the other workflows. Preserve Dashboard as its
  own section and localize menu labels in Armenian, Russian and English.
- Give VCI a separate USB adapter icon, distinct from the diagnostic connector.
  Render Desktop icons at higher resolution for large tiles. CI/CD skipped.

## Unreleased — VIN-first OBD diagnostics

- Raise Symptoms in Desktop and Android navigation and hide its Settings button.
  Keep symptom entry, hypotheses and analysis together. Align Desktop sidebar
  icons and VCI labels; add a diagnostic connector icon.
- Add Diagnostics > Connect OBD and identify vehicle. Desktop uses the selected
  backend adapter; Android uses its native Bluetooth/Wi-Fi/USB bridge, including
  connection before creating a vehicle session. Read VIN first, then display
  responding generic OBD ECUs. Shared backend code validates all responses.
- Disclose online NHTSA VIN lookup before connection. Keep the measured VIN and
  responding modules when lookup is unavailable or incomplete; never infer ABS,
  airbag or other manufacturer blocks from a vehicle name. Simulators do not
  perform online VIN lookup or claim real modules. Restore adapter headers after
  discovery. No DTC clearing, coding, flashing or actuator requests are issued.
- Validated with mocked protocol replies and local Desktop/Android checks.
  Physical vehicle discovery and emulator UI have not been verified here. CI/CD
  is skipped.

## Unreleased — Android default portrait and Live Data settings

- Show the portrait for the currently selected default model/generation without
  requiring another model selection; keep exact-key image invalidation.
- Move Android analog/line display choice into Settings beside EU/USA units.
  Apply both settings to local OBD charts and backend acquisition widgets; keep
  raw measurements unchanged and preserve source/provenance labels.
- Remove repeated per-widget display chips and avoid empty local widgets when
  backend samples are available. Local validation only; CI/CD is skipped.

## Unreleased — Correct fuel names in vehicle selection

- Normalize shared-catalog fuel strings and backend fuel lists before display,
  avoiding Diesel being rendered as D,i,e,s,e,l. Repair known fuel names in
  previously saved letter-split profiles when loading them.
- Preserve multiple fuels such as Petrol + LPG. Local tests only; CI/CD skipped.

## Unreleased — Telemetry display mode in Settings

- Move the analog/line chart choice into Application settings > Widget display.
  Apply the saved choice to all Home and Live Data widgets, including newly
  created widgets. Remove the repeated display-mode dropdown inside each card.
- Preserve border resizing and saved widget dimensions. Local validation only;
  CI/CD is skipped.

## Unreleased — Readable analog widgets with border resizing

- Prevent telemetry cards from shrinking below the height needed for their
  selectors and complete analog dial. Live Data scrolls at the page level.
- Resize each Home/Live Data telemetry card by dragging its right edge, bottom
  edge or bottom-right corner. Save the resulting size per widget without any
  resize buttons, slider controls or extra wrapper panels.
- Keep gauges readable when shrinking and show the correct default RPM scale
  even before samples arrive. Hide empty statistics and the redundant aggregate
  plot to prioritize the per-channel widgets.
- Validated with local geometry, mouse-drag, persistence and Desktop regressions;
  CI/CD is skipped.

## Unreleased — Incoming mobile changes reviewed and integrated

- Preserve the incoming shared-catalog, navigation and backend Live Data changes.
- Fix Android catalog connectivity state, coalesce live refreshes and discard
  stale session responses. Update repository/API test fixtures.
- Invalidate iOS telemetry requests on session changes and display backend
  channel names. Xcode/device execution remains unverified in this environment.
- Review: docs/reviews/android-desktop-parity-2026-10-23.md. Local validation only.

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
