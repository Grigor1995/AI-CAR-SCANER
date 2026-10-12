# AI CAR SCANER — Native Client Feature Contract

This document records the intended shared feature contract for the native PySide6 Desktop, Kotlin/Jetpack Compose Android, and SwiftUI iOS clients. It distinguishes shared backend behavior from platform-specific capabilities and gaps.

## Shared core contract

| Feature | PySide6 Desktop | Native Android | Native iOS | Shared API/data contract |
|---|---|---|---|---|
| Backend connectivity | Yes; configurable backend URL | Yes; shared HTTPS default | Yes; shared HTTPS default and editable URL | Same FastAPI service and session IDs |
| Vehicle catalog and profile | Yes | Yes | Yes | Vehicle catalog and DiagnosticSession |
| Diagnostic session create/read | Create/read active session | Create session; history/reload remains incomplete | Create session; history/reload remains incomplete | POST/GET /api/v1/sessions |
| Symptoms add/edit/delete | Yes | Yes | Yes | Session symptom endpoints |
| DTC add/edit/delete | Yes | Yes | Yes | Session DTC endpoints |
| Deterministic analysis | Yes | Yes | Yes | POST /api/v1/analysis/{session_id}?language=... |
| Evidence, hypotheses, recommendations | Yes | Yes | Yes | Shared DiagnosticSession response |
| Record diagnostic test outcome | Yes | Yes | Yes | PASS, FAIL, INCOMPLETE |
| Activity/audit history | Yes | Yes | Yes | Session audit_log |
| English, Russian, Armenian | Localization parity needs further audit | Localized result labels | Primary labels localized | Backend language codes: en, ru, hy |
| Theme | Dark theme is primary | Light/dark | Light/dark | Client-specific presentation preference |

## Platform-specific capabilities and gaps

| Capability | PySide6 Desktop | Native Android | Native iOS |
|---|---|---|---|
| Live data | Backend telemetry panels and simulator workflow | BLE/Wi-Fi/USB OBD client foundations and Live Data UI | Live OBD data screen not implemented |
| Adapter discovery/connection | Backend device APIs; validate against physical adapters | BLE, Wi-Fi/TCP and USB host code | BLE discovery foundation only; adapter connection and live stream incomplete |
| ECU/network discovery | ECU Network panel and CAN frame/map API calls | Not yet at Desktop parity | Not implemented |
| Reports/export | Reports panel | Not yet at Desktop parity | Not implemented |
| Local AI model runtime | Can use a separately managed local llama-server when configured | Not bundled | Not bundled |

## Result-status contract

- **PASS** — test completed and passed.
- **FAIL** — test completed and failed.
- **INCOMPLETE** — test was not completed or evidence was insufficient.
- New clients must not emit UNKNOWN. The backend temporarily accepts legacy UNKNOWN and normalizes it to INCOMPLETE.
- Armenian labels: ԱՆՑԱՎ / ՉԱՆՑԱՎ / ԱՆԱՎԱՐՏ.
- Russian labels: ПРОЙДЕН / НЕ ПРОЙДЕН / НЕ ЗАВЕРШЁН.

## API URL contract

Default shared API: https://ai-car-scaner.onrender.com

- Desktop: AI_CAR_BACKEND_URL=https://your-api-host
- Android emulator local backend: http://10.0.2.2:8001/ when the backend runs on the development computer.
- iOS: use the API URL setting; for a physical iPhone, configure a reachable Mac/LAN backend URL.

## Release gate

A feature listed in the table is not automatically proof of end-to-end completeness. Before release, test the corresponding UI flow against the configured backend. Simulator/mock telemetry must never be presented as real vehicle/OBD data.

## Client documentation

- [Desktop](apps/desktop/README.md)
- [Android](apps/mobile-android/README.md)
- [iOS](apps/mobile-ios/README.md)
