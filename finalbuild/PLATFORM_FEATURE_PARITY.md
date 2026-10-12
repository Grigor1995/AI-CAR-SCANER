# AI CAR SCANER — Native Client Feature Contract

This document records the shared contract for PySide6 Desktop, Kotlin/Jetpack Compose Android, and SwiftUI iOS. The machine-readable contract is [client_contract.json](config/client_contract.json); update it when shared options or workflow semantics change.

## Shared source of truth

| Concern | Shared contract | Runtime rule |
|---|---|---|
| Vehicle make/model/chassis/year/engine/ECU | `config/client_contract.json` + backend catalog | Online clients request `GET /api/v1/vehicle-catalog/entries`. Backend data is authoritative; any offline fallback must be visibly identified as fallback and never treated as verified fitment. |
| Languages | `en`, `ru`, `hy` | Use the same language codes for UI selection and backend analysis/test-result requests. |
| Theme | `dark`, `light` | Theme is a local presentation preference; native UI controls may differ, but semantic modes must match. |
| Diagnostic workflow | Ordered workflow in JSON | Vehicle → session → symptoms/DTCs → analysis → hypotheses/missing information → tests → PASS/FAIL/INCOMPLETE → re-analysis → activity/close. |
| Test result status | `PASS`, `FAIL`, `INCOMPLETE` | Do not use `INCONCLUSIVE`, `NOT_TESTED`, or `UNKNOWN` as client-facing canonical values. Normalize legacy backend values if needed. |
| Backend | `https://ai-car-scaner.onrender.com` by default | A client may override the URL for local development; use the same API/data contract. |
| App icon | `assets/AI-Car-Scanner.webp` (desktop/mobile WebP) and `assets/ai-car-scanner-icon.png` (iOS source) | All platforms must use the same artwork. Desktop packages `AI-Car-Scanner.ico`; Android launcher WebP is byte-identical to the shared WebP asset; iOS AppIcon uses the PNG artwork. |

## Shared core contract

| Feature | PySide6 Desktop | Native Android | Native iOS | Shared API/data contract |
|---|---|---|---|---|
| Backend connectivity | Configurable backend URL | Shared HTTPS default | Shared HTTPS default and editable URL | Same FastAPI service and session IDs |
| Vehicle catalog and profile | Backend catalog | Backend catalog with a local fallback when the remote catalog is unavailable | Backend catalog | `GET /api/v1/vehicle-catalog/entries` and `DiagnosticSession` |
| Diagnostic session create/read | Create/read active session | Create session; history/reload remains incomplete | Create session; history/reload remains incomplete | `POST/GET /api/v1/sessions` |
| Symptoms add/edit/delete | Yes | Yes | Yes | Session symptom endpoints |
| DTC add/edit/delete | Yes | Yes | Yes | Session DTC endpoints |
| Deterministic analysis | Passes selected language (`en`/`ru`/`hy`) | Passes selected language | Passes selected language | `POST /api/v1/analysis/{session_id}?language=...` |
| Evidence, hypotheses, recommendations | Yes | Yes | Yes | Shared diagnostic response |
| Record diagnostic test outcome | Yes | Yes | Yes | `PASS`, `FAIL`, `INCOMPLETE` |
| Activity/audit history | Yes | Current session audit log only; full session history/reopen incomplete | Current session audit log only; full session history/reopen incomplete | Session `audit_log` |
| Language options | English, Russian, Armenian | English, Russian, Armenian | English, Russian, Armenian | Language codes `en`, `ru`, `hy` |
| Theme | Persistent dark/light preference | Persistent dark/light preference | Persistent dark/light preference | Platform-specific presentation preference, same semantic modes |

## Known parity gaps — do not mark full parity yet

| Capability | Desktop | Android | iOS | Work still required |
|---|---|---|---|---|
| Live telemetry and simulator | UI and backend workflows | Local OBD reader foundations; remote telemetry/simulator parity incomplete | BLE foundation only; live stream/telemetry UI incomplete | Shared telemetry view, simulator controls, connection states, and evidence-source labels |
| Adapter lifecycle | Backend device discovery/connect/reconnect/status and OBD reads | BLE/Wi-Fi/USB client foundations; not all desktop backend device workflows exposed | BLE discovery foundation; connection and streaming incomplete | Same discovery, connect/disconnect/reconnect, VIN, DTC and live-data states |
| ECU/CAN network discovery | Network map, frame ingestion, active probe | Not at Desktop parity | Not implemented | Shared network-discovery screen and safe operation controls |
| Session history and reopen | Local store and session reads | Not implemented end-to-end | Not implemented end-to-end | Persist session IDs, list/reopen sessions, refresh server state, and close/archive consistently |
| Reports/export | Reports panel | Not at Desktop parity | Not implemented | Common report schema and export/share on each platform |
| Local AI provider status/live-data AI | Provider status and live-data AI endpoint | Not exposed in app UI | Not exposed in app UI | Provider availability/error state, timeout handling and AI result display |
| UI localization completeness | Settings persist language, but the full Desktop UI is not translated | English/Russian/Armenian strings available | English/Russian/Armenian strings available | Complete and test all Desktop strings; audit terminology across platforms |
| Vehicle catalog parity offline | Backend catalog | Local fallback may differ from backend catalog | No matching offline catalog guarantee | Shared catalog snapshot/versioning and visible stale/offline state |

**Definition of done for full functional parity:** each row above must be implemented on all three platforms, use the same API semantics and status values, have automated contract/UI tests, and pass the release matrix on actual build runners. A matching feature label or shared API alone is not proof of parity.

## Result-status contract

- **PASS** — test completed and passed.
- **FAIL** — test completed and failed.
- **INCOMPLETE** — test was not completed or evidence was insufficient.
- Legacy backend `UNKNOWN` values must be normalized to `INCOMPLETE` at the client boundary.
- Armenian labels: ԱՆՑԱՎ / ՉԱՆՑԱՎ / ԱՆԱՎԱՐՏ.
- Russian labels: ПРОЙДЕН / НЕ ПРОЙДЕН / НЕ ЗАВЕРШЁН.

## API URL contract

- Default shared API: `https://ai-car-scaner.onrender.com`
- Desktop: `AI_CAR_BACKEND_URL=https://your-api-host`
- Android emulator local backend: `http://10.0.2.2:8001/`
- iOS physical device: configure a reachable Mac/LAN backend URL in Settings.

## Icon implementation

- Desktop executable: `assets/AI-Car-Scanner.ico` (packaged by PyInstaller specs).
- Android launcher: `apps/mobile-android/app/src/main/res/mipmap/ic_launcher.webp`; its Git blob is identical to `assets/AI-Car-Scanner.webp`.
- iOS: `apps/mobile-ios/AICarScanner/Assets.xcassets/AppIcon.appiconset`, configured as `AppIcon` in XcodeGen.
- The source art is shared; platform-specific file formats and required icon packaging are expected.

## Release gate

A feature listed here is not proof of end-to-end completeness. Test the corresponding UI flow against the configured backend before release. Simulated/mock telemetry must never be presented as real vehicle/OBD data. CI/builds must execute on real runners; a job with no runner and zero steps is not a passing test.

## Client documentation

- [Desktop](apps/desktop/README.md)
- [Android](apps/mobile-android/README.md)
- [iOS](apps/mobile-ios/README.md)
