# Native feature parity implementation — 27 October 2026

Implements the gaps found in [the source audit](native-functional-parity-2026-10-27.md).
The core application/diagnostic operations are exposed through the common backend.
Native clients retain their UI, preferences and byte transports. No CI/CD was run.

## Changes

| Area | Implementation |
|---|---|
| Shared vehicles | Backend `/api/v1/vehicle-profiles` list/create/update/delete; controls on all three clients. Desktop retains existing local profiles for compatibility and offline use; upload/import is explicit. |
| Reports | Backend `/api/v1/sessions/{id}/report?format=json|pdf&language=en|ru|hy`; all three clients can export it. Searchable Unicode font is packaged with the backend, including its license. Session/device binding IDs are removed recursively. Desktop's existing offline/native export and mobile share actions remain available. |
| Acquisition | Android/iOS expose simulator start, parameter updates and stop, plus server-connected real adapter acquisition. Canonical parameters are RPM, coolant °C, speed km/h and throttle %. These controls never change a real vehicle's parameters. |
| Telemetry / AI | Android/iOS expose summary, telemetry evidence analysis and live AI interpretation, diagnostic decision/missing-information plan and provider status. The backend performs all reasoning. |
| ECU map | Android/iOS expose the existing passive/inferred map and active read-only probe. A map is not a promise that every proprietary ECU is reachable through generic OBD. |
| Repair references | Mobile can now ingest reference material into the same backend as Desktop. Draft/share remains available. This is knowledge ingestion, not model training. |
| Desktop input editing | Recorded symptoms and DTCs can be edited/deleted through backend routes and then reanalyzed. New combined input uses the same symptom route as mobile. |
| Mobile Live Data | iOS gains analog/line preference, mph/°F display conversion, visible-channel selection and edge resizing. Android gains MAF/STFT/LTFT selection and edge resizing. Display conversions never rewrite source measurements. |
| iOS Diagnostic | A dedicated VIN/responding-ECU screen replaces the duplicate VCI route. Wi-Fi and BLE use backend discovery commands and restore steps. Discovery and polling are serialized; disconnect cancels pending reads. |
| iOS Wi-Fi polling | Continuous cancellable polling scoped to active session; disconnect/server/session changes invalidate readings. Backend records continue to refresh independently. |
| Native BLE | iOS and Android support GATT UART byte exchange for FFE0/FFE1, FFF0/FFF2/FFF1 and Nordic UART service profiles. The profile is identified from GATT services/characteristics, not the adapter name. Unsupported profiles fail explicitly. No BLE protocol decoding lives in the client. |
| Backend-host adapters | Both mobile clients can discover/manage adapters attached to Backend, identify their vehicle and start real acquisition from the selected adapter. This provides the USB path for iOS without inventing an unsupported native USB implementation. |
| Runtime backend choice | Android now saves an API URL and reopens its Activity task with fresh repositories/session state. iOS applies a validated API URL and clears the active session. Desktop saves the URL for its next launch; explicit `AI_CAR_BACKEND_URL` takes precedence. |
| Test progress | iOS now counts only the latest PASS/FAIL results for current recommendation IDs; INCOMPLETE stays open, matching Desktop/Android. |

New mobile backend controls are expandable, so they do not displace the normal
charts/menu with a permanently expanded form. Settings remain in the application
menu. No movement buttons/sliders or CI/CD workflows were added.

## Where to find the controls

- **Main menu → Shared vehicles**: open the expandable section, refresh the list,
  save the current vehicle, use a saved vehicle or replace/delete an entry.
  Desktop uses Vehicles → Shared vehicles and an ordinary native editor.
- **Live Data → Acquisition / telemetry**: simulation/server acquisition controls,
  canonical input values, telemetry summary and AI interpretation.
- **Diagnostic → ECU network**: map and probe. **VCI → Server adapters** manages
  adapters physically attached to the backend host. Native phone adapters remain
  in the ordinary Bluetooth/BLE/Wi-Fi/USB section.
- **AI Analysis → Diagnostic plan**: backend decision plan and AI-provider status.
- **Reports → Export report**: download/share the common PDF or JSON report.
- **Teach AI → Send repair reference**: submit verified text to backend knowledge.
- On mobile, drag the bottom edge area of a Live Data card to change chart height.
  Saved sizes and unit/display preferences are local UI settings.

## Installation and backend requirements

Update **both the backend and the native client**, then install backend dependencies:

```bash
cd finalbuild
python -m pip install -r backend/requirements.txt
python -m apps.desktop.main --with-backend --local-ai
```

All clients must use the same reachable API server to share sessions and saved
vehicles. On a phone, `127.0.0.1` refers to the phone, not the Desktop backend.
Use the computer's LAN address and the configured listening port (normally 8001).
On Android emulator, `10.0.2.2:8001` refers to the host. The backend must listen on
a reachable interface when serving another device. Merely pushing Git commits
does not deploy a separately hosted backend service.

Vehicle profiles use the configured `DATABASE_URL` and a separate SQLAlchemy
`vehicle_profiles` table. In the explicit no-database development mode, they
are process-memory only, like sessions. No existing local vehicle file is deleted
or automatically uploaded. Use the shared-vehicle controls to migrate selected
profiles. Profiles and sessions must be backed up together for persistent use.

The new PDF route requires ReportLab and the bundled DejaVu font; frozen backend
packaging already includes the backend resource tree. The standalone desktop
GUI continues to use its existing native export when offline.

## Validation and remaining physical acceptance

- Full Python repository regression: recorded in the final validation update below.
- Desktop five-group regression and both 90% coverage gates: recorded below.
- Android JVM suite, debug APK, instrumentation compilation and lint: recorded below.
- Swift files and XCTest sources pass syntax-tree validation. New XCTest contracts
  cover backend discovery, operation routing, display conversion and private output.
  **Xcode type checking, XCTest execution, signing and iOS runtime acceptance were
  not available in this Linux environment.** Syntax validation is not an iOS build.
- BLE/Wi-Fi/USB hardware communication is implemented but **not physically verified**
  by these checks. Validate connection, supported PIDs, VIN, dropouts, reconnect,
  page/session switching and EN/RU/HY behavior with the actual adapters and car.
- iOS cannot use ordinary classic Bluetooth SPP ELM adapters or arbitrary USB
  serial accessories directly. Use a supported BLE UART/Wi-Fi adapter, or an
  adapter attached to Backend. No MFi/ExternalAccessory protocol is claimed.
- Manufacturer-specific ECU diagnostics still depend on real protocol/adapter
  support; the common UI does not manufacture proprietary ECU coverage.

## Final validation results

| Scope | Result |
|---|---|
| Python repository tests (`tests`) | 889 passed, 2 skipped |
| Desktop regression groups | All five groups pass; 445 passed, 1 skipped across group executions |
| Desktop source / production-core statement coverage | 90.45% / 90.79%; both exceed 90% |
| Android JVM | 113 passed; 0 failures/errors/skips |
| Android build | Debug APK and instrumentation sources compile |
| Android lint | 0 errors, 21 warnings |
| Swift syntax | 19 source/test files parse successfully |
| iOS native build and physical OBD | Not executed; requires Xcode and actual hardware |

These are scoped checks, not a claim of 100% coverage or verified support for
every commercial OBD adapter. Python and Desktop groups overlap; do not add
their counts as unique tests. The added common API integration test exercises
simulator start → SI parameter update → collected records → telemetry analysis
→ ECU map request → Armenian PDF export → stop.
