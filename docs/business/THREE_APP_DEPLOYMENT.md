# Three apps, one shared backend

2026-10-29. Current deployment structure in AI-CAR-SCANER.

| Product | Desktop entry / executable | Android ID | iOS bundle ID |
|---|---|---|---|
| USER | `apps.user.main` / `AI-Car-User.exe` | `com.aicarscaner.user` | `com.aicarscaner.user` |
| CUSTOMER | `apps.customer.main` / `AI-Car-Customer.exe` | `com.aicarscaner.customer` | `com.aicarscaner.customer` |
| MARKET | `apps.market.main` / `AI-Car-Market.exe` | `com.aicarscaner.market` | `com.aicarscaner.market` |

These are three independently installed applications per platform, with fixed
workspaces and isolated application settings/sandboxes. Each uses the existing
visual palette and icon. Shared presentation code is reused; backend rules are
not copied into the three clients. MARKET remains a merchant portal entitlement,
not a fourth primary diagnostic mode. ADMIN management stays in protected backend
APIs; no fourth ADMIN app is generated.

## One physical backend location

`finalbuild/backend/` owns API, identity/consent, diagnostics/AI, telemetry, device
management, reports, SQL/migrations, canonical vehicle/protocol stack and service
lifecycle. New independent entry: `backend/main.py`; low-level server: `server.py`.
Vehicle implementation moved from `finalbuild/vehicle/` to `backend/vehicle/`.
Old simulator compatibility modules moved to `backend/legacy_vehicle/` so they
cannot shadow the real protocol stack. Explicit historical `backend.vehicle`
imports retain simulator compatibility; production `vehicle` imports resolve to
the canonical backend directory regardless of path ordering. GUI launcher backend
lifecycle moved from `apps/desktop/main.py` to `backend/desktop_runtime.py`.
Portable PDF rendering moved from shared/reporting.py to backend/reporting.py.

The old Desktop worker/main, root vehicle package and shared reporting are tiny
compatibility exports, not second implementations. Legacy developer tooling is
retained for existing local diagnostics and tests; it is not a fourth packaged
product. Static data, image assets, shared ENV configuration and native hardware
bridge/firmware sources remain outside the backend because they are resources or
client/platform responsibilities, not duplicate diagnostic/business engines.

The shared server does not import Desktop UI to run. Optional local AI startup
uses the centralized legacy runtime's model/server lifecycle without invoking its
GUI function. Backend executable packaging explicitly excludes PySide6/UI modules.
New Desktop clients never start/stop backend or AI processes. Closing one client
leaves the shared server and other clients running.

## Local setup and run (Windows Git Bash)

From the repository root:

```bash
cd ~/Desktop/AI-CAR-SCANER/git
git pull --ff-only origin main
python runner.py setup --skip-ai
```

Start one backend in its own terminal:

```bash
python runner.py backend --migrate
```

If continuing the previously created `business.sqlite`, explicitly keep it:

```bash
python runner.py backend --database ./business.sqlite --migrate
```

With no explicit path or DATABASE_URL, the backend creates its own persistent
`AI-Car-Backend/business.sqlite` under APPDATA (Windows), XDG_DATA_HOME or
~/.local/share (Linux). An explicitly configured DATABASE_URL is preserved.
No accounts, anonymous profiles or old databases are silently copied/reassigned.
`--migrate` explicitly applies existing additive migrations; take a backup first
for an existing installation. Run only one backend on the selected port.
Optional existing GGUF/llama-server startup: add `--local-ai`. No model download is
performed by backend startup. Remote inference configuration remains server-owned.

Open separate Desktop clients in other terminals:

```bash
python runner.py desktop --app user
python runner.py desktop --app customer
python runner.py desktop --app market
```

Use `--backend-url http://HOST:8001` for a separately hosted backend. Backend URLs
are saved per Desktop app. Tokens/passwords are memory-only. A new CUSTOMER or
MARKET account can register a workshop/shop after login; the server grants the
matching entitlement only through that existing business-registration operation.
No app build flag grants server privileges.

Android with an already running emulator:

```bash
python runner.py android --app user --api-url http://10.0.2.2:8001/
python runner.py android --app customer --api-url http://10.0.2.2:8001/
python runner.py android --app market --api-url http://10.0.2.2:8001/
```

All three can coexist; runner launches the shared activity class with each
variant's distinct package ID. Backend URL can also be edited before mobile login
and persists inside that app's sandbox. Existing old `com.aicarscaner.mobile`
installation is not automatically uninstalled because it may contain local data.
Back up/import existing data before manually removing that legacy installation.

On macOS: generate the Xcode project from apps/mobile-ios/project.yml, then select
AICarScannerUser, AICarScannerCustomer or AICarScannerMarket. Each target has its own
bundle ID/display name and app-owned backend URL setting. iOS simulator default
is http://127.0.0.1:8001; a physical device needs the configured reachable server.
Xcode signing/store distribution must be configured on macOS.

## Build artifacts

```bash
python build.py --targets desktop android --with-tests
```

Builds all three products by default. Select a subset with `--apps user customer`
or `--apps market`. Outputs are under artifacts/<timestamp>/ with SHA-256 records
in build-summary.json. Windows output: three independent client ZIPs plus one
shared headless backend ZIP. Backend is not duplicated inside each client archive.
Android output: AI-Car-User-Android-debug.apk, AI-Car-Customer-Android-debug.apk,
AI-Car-Market-Android-debug.apk. iOS builds on macOS emit three simulator app ZIPs;
these are not signed IPAs. Windows source installer now creates three app shortcuts
and forwards their fixed --app choice; shared backend is started independently.

## Actual scope and validation

This separates deployment identities and centralizes code. The previously noted
business UI limitations remain: authenticated account/workspace reads and business
onboarding work, while complete native diagnostic/inventory/order/consent editing
forms are still partial. Existing full legacy diagnostic UI remains available to
developers through `runner.py desktop --legacy`, not an extra shipped application.
Providers/licensed data remain unavailable as confirmed by the user. No active
payments or CI/CD added.

Executed QA and real APK identity hashes: evidence/three-app-qa.json and
evidence/three-app-android-artifacts.json. Linux Desktop smoke tests open/close
all three real Qt apps and verify no FastAPI/SQLAlchemy/backend imports. Real
central server HTTP smoke verifies all three workspaces against one DB, business
onboarding, denied wrong-role access, and restart persistence. Android compiles
all three APKs and instrumentation source sets, runs JVM/lint. Device installation
and physical OBD were NOT RUN. Windows EXE/installer and iOS builds are NOT VERIFIED
on this Linux host; build orchestration/configuration tests do not imply otherwise.

## Executed verification snapshot

- Full common suite: **1105 passed, 2 skipped**, 63.93 s.
- Final deployment/build/installer/SQLite focused suite: **103 passed**.
- Desktop: all five groups PASS; source coverage **90.06%**, production core
  **90.36%**, enforced >=90%, including new product/workspace modules.
- Three real Qt app windows open/close without backend/FastAPI/SQLAlchemy imports;
  additional in-process UI tests verify threaded login success/error and fixed roles.
- Android: **199 tasks**, 63 executed/136 cached, **2m59s**. All three APKs compiled,
  each has **113 JVM tests**, zero failures/errors. Instrumentation source compiled,
  device/emulator installation NOT RUN. Actual APK IDs/names verified with aapt.
- Independent backend: **20 real HTTP/restart checks PASS** on one temporary SQL DB.
- Canonical source preservation: 81 vehicle/legacy source moves verified against
  baseline, plus separate runtime/worker/report mappings. Only import/resource
  bootstraps adapted; no diagnostic engine rewrite.
- Windows executable/installer and iOS build are NOT VERIFIED here. Docker NOT RUN.

The previous old package/combined developer entry is retained for data-safe
compatibility, not included as a fourth product in the new default builder. No
user database or old mobile installation was deleted during this change.
