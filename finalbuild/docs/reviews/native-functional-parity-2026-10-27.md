# Desktop / Android / iOS functional parity audit — 27 October 2026

Reviewed source: `6b6c2bf` (also origin/main when inspected). This audit checks
implemented actions and data paths, not just matching page names. No application
behavior was changed. No CI/CD was used.

**Conclusion: the three clients are not functionally equivalent.** The shared
session/analysis/test-result workflow is implemented in all three, but Desktop
has several backend operations missing from mobile, and iOS has significant
transport, diagnostic-discovery and Live Data gaps.

## Capability matrix

“Present” means a source-level UI-to-handler/API path exists; it does not imply
physical-device acceptance. All clients must target the same backend deployment
and session for their diagnostic state to be comparable.

| Capability | Desktop | Android | iOS |
|---|---|---|---|
| Shared bundled selection catalogue and generation artwork | Present | Present | Present |
| Create session, edit active vehicle | Present | Present | Present |
| Independent local saved-vehicle profiles / deletion | Present | No equivalent profile store/UI | No equivalent profile store/UI |
| Symptoms/DTC input | Evidence-text ingestion + DTC add | Symptom and DTC CRUD | Symptom and DTC CRUD |
| Edit/delete individual symptoms and DTCs | No matching CRUD controls/API-client methods | Present | Present |
| Analysis, hypotheses, recommendations | Shared backend | Shared backend | Shared backend |
| PASS / FAIL / INCOMPLETE and score recalculation | Shared result endpoint | Same endpoint | Same endpoint |
| Selected response language | EN/RU/HY, reload active analysis | EN/RU/HY, reload active session | EN/RU/HY, reload active session |
| History / reopening sessions / audit events | Present | Present | Present |
| Installed application branding / main menu reorder | Present | Present | Present |
| Native/backend Wi-Fi OBD data path | Backend device manager | Native TCP byte bridge | Native TCP byte bridge |
| Bluetooth OBD data path | Backend transport, host dependent | Paired classic Bluetooth/RFCOMM | BLE scanning only; no connect/GATT OBD exchange |
| USB OBD | Backend serial/USB, host dependent | Native USB driver path | No implemented accessory transport |
| VIN-first discovery and observed ECU responders | Dedicated Diagnostic action | Dedicated Diagnostic action | Missing; Diagnostic and VCI open the same view |
| Continuous locally connected OBD polling | Backend acquisition loop | Native coroutine loop | Connect/Read requests one batch; backend-records view refreshes separately |
| Stored backend Live Data | Present | Present | Present |
| Analog/line mode and EU/USA units | Present | Present | Line chart only; no corresponding settings |
| User-selected Live Data widgets | Add widgets, edge resizing | Select visible channels | No equivalent picker/resizing |
| Simulator start/stop and editable parameter values | Present | No equivalent UI/API path | No equivalent UI/API path |
| Telemetry summary / telemetry analysis / live AI analysis | Dedicated backend calls | No equivalent API calls | No equivalent API calls |
| ECU network map / active read-only probe | Present | No equivalent UI/API calls | No equivalent UI/API calls |
| Reports | Native PDF export and history | Share JSON report text | Share JSON report text |
| Teach AI / repair knowledge | Reference ingestion into backend; not model training | Local structured draft and share | Local title/draft and share |
| Managed local backend and GGUF server startup | Desktop command-line options | Uses configured remote/LAN backend | Uses configured remote/LAN backend |
| Backend URL selection | Runtime configuration | Build-time Gradle `apiBaseUrl` | Runtime Settings API URL |

## Findings, with source evidence

### 1. High: iOS Bluetooth is discovery-only

`apps/mobile-ios/AICarScanner/OBDService.swift:4` implements central state and BLE
scan callbacks. There is no connection callback, GATT service/characteristic
selection, write operation or notification/read pipeline. Device rows in
`DiagnosticScreen.swift:491` are text, not connect actions. Seeing a BLE device
is therefore not proof of OBD support. Android's Bluetooth path is classic
RFCOMM, so the two platforms do not support an identical adapter family.
USB on iOS also needs a suitable Apple-supported accessory implementation;
Android's USB driver cannot simply be shared with iOS.

### 2. High: iOS Diagnostic is a duplicate route, not VIN-first diagnostics

`DiagnosticScreen.swift:80` and `:82` both route Diagnostic and VCI to `obdView`.
`DiagnosticAPI.swift` has PID plans/decoding but no discovery-plan/decode methods.
Desktop `ui.py:952` and Android `DiagnosticScreen.kt:544` actually run vehicle
identification and show observed responders. A matching menu label masks this gap.

### 3. High: iOS Live Data lacks key controls and native continuous polling

`DiagnosticScreen.swift:319` draws `LineMark` charts in received units.
`DiagnosticModels.swift:163` settings contain language, theme and API URL only.
There is no analog-display or EU/USA preference/conversion path, no channel
selection and no widget-size control. `DiagnosticViewModel.swift:18` calls the
Wi-Fi bridge once per button press. The two-second loop at `DiagnosticScreen.swift:345`
refreshes backend records; it does not repeatedly poll the native Wi-Fi adapter.
Android's connected adapter loop is at `DiagnosticScreen.kt:600`; Desktop uses
backend acquisition. These are materially different behaviors.

### 4. Medium: Android local charts omit three decoded channels

`data/obd/LiveDataReader.kt:3` models ten decoded fields, including MAF, STFT and
LTFT. The local `channels(history)` list in `presentation/DemoPanels.kt:190`
contains only seven: RPM, coolant, MAP, speed, load, intake temperature and throttle.
The three omitted fields cannot be added through the local-history widget picker.
Stored backend charts use a separate dynamic records path, so this finding is
specific to local native-history charts, not all backend record display.

### 5. Medium: Desktop-only backend capabilities are not exposed in mobile

Desktop `api_client.py` and its UI invoke acquisition start/stop, simulator
parameter updates, telemetry summary/analysis, live AI analysis, network map,
active probe and reference ingestion. The Android `DiagnosticApi.kt` and iOS
`DiagnosticAPI.swift` lack these operations. Viewing records or opening a similarly
named page is not an implementation of these controls.
`demo_ui.py:592` actually submits Teach AI reference material; Android
`DemoPanels.kt:405` and iOS `DiagnosticScreen.swift:377` only persist/share drafts.
None of these actions trains a model.

### 6. Medium: editing and persistence differ in both directions

Mobile has symptom/DTC update/delete routes; Desktop only exposes the combined
input workflow and DTC add. Conversely, Desktop `ui.py:1887` deletes independent
local vehicle profiles; mobile edits the active session's vehicle. This is not
the same saved-vehicle lifecycle. A common backend vehicle-profile contract is
needed if profiles must be identical across devices.

### 7. Medium: reporting, configuration and localization are not identical

Desktop PDF export is not available through the mobile JSON share actions.
Android API base URL is compiled from Gradle (`app/build.gradle.kts:26`), whereas
iOS allows editing it at runtime. This can cause apparently different results
when installations actually use different servers.

All three analysis/result requests carry the selected language and reload the
active session on language changes. This does not establish complete translation:
iOS BLE statuses in `OBDService.swift`, most Wi-Fi bridge errors in
`NativeObdWifiBridge.swift:28`, and iOS chart axis keys remain English. Desktop
network-map labels in `ui.py:1422` and mobile raw audit-event names also need a
separate rendered-language acceptance pass.

## Shared reasoning: what is verified

Desktop `ui.py:2100`, Android `DiagnosticViewModel.kt:150`, and iOS
`DiagnosticAPI.swift:194` submit results to
`POST /api/v1/intelligence/sessions/{id}/test-results`. They consume its returned
session rather than maintaining independent client-side hypothesis scoring.
`tests/ai/test_test_result_scores.py` verifies PASS/FAIL score direction,
replacement of prior results, INCOMPLETE withdrawing an outcome, accumulation
across distinct tests and persistence across repeated analysis/localization.

This supports shared reasoning for the same backend session and inputs. It does
not prove identical end-to-end behavior for separately created sessions: Desktop
text-evidence ingestion and mobile symptom CRUD use different input operations.

## Checks executed for this audit

| Check | Result |
|---|---|
| Shared catalogue, icon parity, result-score reasoning, OBD bridge/protocol contracts, Desktop artwork | 78 passed |
| Desktop UI POM subset: result/live/settings/diagnostic/launcher | 35 passed; 93 deselected |
| Android JVM suite | 110 tests; 0 failures/errors/skips; Gradle success |
| Android/iOS real-device OBD | Not executed; no physical adapter/car |
| iOS build / XCTest / Simulator | Not executed; no Xcode environment |
| Full three-client end-to-end comparison | Not executed |

Test success is scoped to these checks; it is not a claim of complete coverage
or full functional parity. Source audit includes iOS, but iOS runtime behavior
still needs Xcode and device acceptance.

## Recommended development order

1. Implement iOS VIN discovery and a continuous Wi-Fi polling lifecycle with
   cancellation/disconnect, then validate it on a real adapter.
2. Add iOS analog/line, EU/USA display preferences and selectable channels; expose
   MAF/STFT/LTFT in Android local-history charts.
3. Expose common simulator, telemetry/live-AI, network-map and reference-ingestion
   operations through the mobile API clients and screens.
4. Define a shared saved-vehicle lifecycle, symptom/DTC editing contract, report
   formats and runtime backend selection.
5. Run identical seeded-session scenarios on all three clients, followed by
   transport-specific hardware acceptance and EN/RU/HY rendering checks.
