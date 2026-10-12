# AI CAR SCANER — Single Cross-Platform Feature Contract

This is the canonical feature list for Flutter Desktop, native Android, and native iOS. Keep this document as the single source of truth instead of maintaining conflicting feature lists in individual app READMEs.

## Shared core contract

| Feature | Flutter Desktop | Native Android | Native iOS | Shared API/data contract |
|---|---|---|---|---|
| Backend connectivity | Yes; HTTPS Render default, API_URL override | Yes; HTTPS Render default | Yes; HTTPS Render default, editable in Settings | Same FastAPI service and session IDs |
| Vehicle catalog and vehicle profile | Yes | Yes | Yes | GET vehicle catalog; create/update vehicle in DiagnosticSession |
| Diagnostic session create/read | Create/read active session | Create session; history/reload is incomplete | Create session; history/reload is incomplete | POST/GET /api/v1/sessions; native clients still need a session-history/load UI |
| Symptoms add/edit/delete | Yes in Flutter Desktop | Yes | Yes | POST/PUT/DELETE /api/v1/sessions/{id}/symptoms |
| DTC add/edit/delete | Yes in Flutter Desktop | Yes | Yes | POST/PUT/DELETE /api/v1/sessions/{id}/dtcs |
| Deterministic analysis | Yes | Yes | Yes | POST /api/v1/analysis/{session_id}?language=... |
| Evidence, hypotheses, recommendations | Yes | Yes | Yes | Shared DiagnosticSession response |
| Record diagnostic test outcome | Yes; candidate test plan + result dialog | Yes | Yes | Canonical values are PASS, FAIL, INCOMPLETE |
| Activity/audit history | Yes | Yes | Yes | Shared session audit_log |
| English, Russian, Armenian | Not yet at native-client localization parity | Yes; result labels localized | Yes; primary labels localized | Backend language codes: en, ru, hy; full-screen localization audits still required |
| Light/dark theme | Dark theme currently the primary Flutter theme | Yes | Yes | Presentation preference is client-specific |

## Platform-specific capabilities and known gaps

| Capability | Flutter Desktop | Native Android | Native iOS |
|---|---|---|---|
| Live Data | Backend telemetry/acquisition panels and simulator workflow | Bluetooth/Wi-Fi/USB OBD clients and Live Data UI | Not implemented as a live OBD data screen yet |
| OBD adapter discovery/connection | Uses backend device APIs in the Python legacy client; Flutter parity is incomplete | BLE, Wi-Fi/TCP and USB host code | BLE discovery only; connection and Wi-Fi/TCP OBD transport are incomplete; generic USB is not implemented |
| ECU/network discovery | ECU Network panel and CAN frame/map API calls | Not at Flutter Desktop feature parity | Not implemented |
| Reports/export | Reports panel | Not at Flutter Desktop feature parity | Not implemented |
| Local AI model runtime | Python legacy Desktop can start local llama-server when local backend mode is explicitly configured | Not included in native app | Not included in native app |

## Result-status contract

- PASS — test completed and passed.
- FAIL — test completed and failed.
- INCOMPLETE — test was not completed or did not produce enough evidence.
- New clients must not emit UNKNOWN. The backend accepts legacy UNKNOWN temporarily and normalizes it to INCOMPLETE.
- User-facing Armenian labels: ԱՆՑԱՎ / ՉԱՆՑԱՎ / ԱՆԱՎԱՐՏ.
- User-facing Russian labels: ПРОЙДЕН / НЕ ПРОЙДЕН / НЕ ЗАВЕРШЁН.

## API URL contract

Default shared API: https://ai-car-scaner.onrender.com

- Flutter Desktop override: --dart-define=API_URL=https://your-api-host
- Python legacy Desktop override: AI_CAR_BACKEND_URL=https://your-api-host
- Android development emulator can use http://10.0.2.2:8001/ only when the backend is running on the development computer.
- iOS Settings supports an API URL override. Existing saved localhost:8001 values are migrated to the shared Render URL.

## Release gate

Before calling the three clients feature-parity complete, add/enable automated tests for each shared contract row and implement the platform-specific gaps above. A listed API method alone does not mean the user-facing feature is complete. Do not claim real OBD data when using simulator or mock telemetry.

## Related client documentation

- Desktop Flutter: apps/desktop/README.md
- Android: apps/mobile-android/README.md
- iOS: apps/mobile-ios/README.md
