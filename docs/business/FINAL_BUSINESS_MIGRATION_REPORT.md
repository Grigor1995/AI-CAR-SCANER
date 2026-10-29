# Final Business Migration Report

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

This is a functional incremental business migration, NOT the complete target
enterprise product. Existing project/UI/icons/AI/OBD/legacy local APIs remain.
No CI/CD, payment gateway or new production C++ dependency introduced.

Actual implemented backend capabilities:
- Scoped persistent canonical diagnostic sessions, evidence/test result engine reuse
  and recalculation, history, read-only plans and timestamped observed native data.
- Explicit diagnostic/maintenance consent scopes, accepted staff invitations,
  work-order status/notes, actual scoped workshop counts, verified directory.
- Owned merchants/products/inventory, admin verification/moderation, non-stacking
  server-side percentage/time/quantity/coupon/customer/center price quotes;
  unverified fitment labeled honestly; no active checkout.
- Audited ADMIN status/role governance with session revocation and private data
  restrictions. Explicit local first-admin bootstrap, no public privilege bypass.
- Persistent owner schedules and idempotent deferred/missed runs/in-app notices;
  no actual autonomous gateway scan or external notification success claim.
- Account preferences including French, typed shared engineering conversions and
  EN/HY/RU/FR errors/navigation. Full native French localization remains partial.
- Three native account browsers: create account, login/logout and permitted reads.
  Full business editing/diagnostic-screen integration remains PARTIALLY IMPLEMENTED.

Exact source groups:
backend/ecosystem/business_models.py (12 additive aggregates), business_schemas.py
(strict request/critical output contracts), business_service.py (object/consent,
shared diagnostics, pricing/settings/schedule rules), business_api.py (authenticated
workflow boundary), units.py; api.py (router install + stale save conflict),
schemas.py (explicit new scopes), service.py (duplicate pending invite rejection),
errors.py (French), migrations/env.py + versions/0002_business_workflows.py.
Desktop ui.py adds application-menu entry and business_workspace.py, plus boundary
tests. Android DashboardNavigation.kt/DiagnosticScreen.kt add menu sheet and
BusinessWorkspace.kt. iOS DiagnosticScreen.swift/BusinessWorkspace.swift match the
account browser, unverified without Xcode. Tokens/passwords are memory-only.
bootstrap_business_admin.py is explicit local operator setup. Shared smoke helper
now verifies diagnostic/settings restart persistence. Business tests and migration
head assertion extended. Existing diagnostic algorithms/icons were not replaced.

See evidence/ for executed QA, coverage, database/API smoke and browser results.
See IMPLEMENTATION_PLAN for remaining work. The complete master definition of
done is NOT met for native editing, verification/delivery providers, unattended
hardware, licensed wiring/fitment, full translations and production deployment.

## Local run — new business APIs

From Windows Git Bash at repository root (keep cwd unchanged):

```bash
cd ~/Desktop/AI-CAR-SCANER/git
git pull --ff-only origin main
python runner.py setup --skip-android --skip-ai
source .venv/Scripts/activate
export DATABASE_URL='sqlite:///business.sqlite'
python -m alembic -c finalbuild/backend/alembic.ini upgrade head
export AI_CAR_ECOSYSTEM_ENABLED=1
export AI_CAR_BACKEND_HOST=127.0.0.1
export AI_CAR_BACKEND_PORT=8001
python finalbuild/apps/desktop/backend_worker.py
```

Open http://127.0.0.1:8001/docs locally. Register/login; Authorize with raw bearer
access_token. Use business-ecosystem endpoints and foundation vehicle/consent APIs.
Register an account FIRST, then in another shell with same DATABASE_URL/cwd:
python finalbuild/scripts/bootstrap_business_admin.py --email YOUR_EMAIL --grant-admin.
Never run migrations against a different relative SQLite directory.

Native account browser: configure backend URL to this running instance. Desktop
Application menu → USER/CUSTOMER/ADMIN • MARKET; Android/iOS application ⋮ menu.
Legacy diagnostic screens are incompatible with ecosystem mode by design; they
still work in default local mode. Do not describe the new browser as complete
native business workflow support. For existing normal Desktop, stop business
backend then unset DATABASE_URL; export AI_CAR_ECOSYSTEM_ENABLED=0;
python runner.py desktop --no-ai. Android emulator uses 10.0.2.2:8001 or adb reverse.

Open docs/architecture/business_architecture_dashboard.html for bundled interactive
before/after architecture and permissions. No CDN or runtime statistics invented.

## Desktop account browser against the running business backend

In a second Git Bash terminal:

```bash
cd ~/Desktop/AI-CAR-SCANER/git
source .venv/Scripts/activate
export AI_CAR_BACKEND_URL='http://127.0.0.1:8001'
cd finalbuild
python -m apps.desktop.main --no-backend
```

Open Application → USER/CUSTOMER/ADMIN • MARKET. The business account browser
can register/sign in/read authorized data. Legacy diagnostics in this instance
remain blocked by the authenticated backend boundary; no UI parity completion
is claimed. Keep migrations/backend launch in repository-root terminal so the
relative business.sqlite path stays consistent.

## Executed QA

- Full common suite: **1091 passed, 2 skipped**, 69.19 s.
- Ecosystem line+branch coverage: **98.06%**, enforced >=90%.
- Desktop five isolated groups: **PASS**, source 90.49% / core 90.76%.
  Final switch to existing requests transport: 2 additional boundary tests PASS.
- Android: **BUILD SUCCESSFUL**, 67 tasks (17 executed, 50 cached), 1m43s;
  Kotlin + instrumentation source compile + JVM tests + APK + lint. No device run.
- Real temporary SQLite/Uvicorn HTTP + restart: **15 checks PASS**.
- Actual Chromium business dashboard: **11 checks PASS**: views/layers/search,
  collapse, permissions/dependencies, zoom/pan/wheel, 420px responsiveness.
- PostgreSQL offline migration DDL PASS; live PostgreSQL NOT RUN.
- Ruff selected correctness checks / JS syntax / Git whitespace: PASS.
- iOS Xcode, Windows packaging, real adapter/gateway/providers: NOT RUN/BLOCKED.

One original source snapshot test expected the old iOS settings-only overflow
menu. Updated it to verify settings and the new business action remain inside
the same overflow menu. No settings affordance moved into the main dashboard.
The initial Android compile caught OkHttp 3 vs 4 helper incompatibility; changed
the account browser to the installed OkHttp 3 API and rebuilt successfully.

Snapshot raw evidence is in evidence/. Full target completion is not claimed.

External prerequisites confirmed by user: no email/SMS/push provider or licensed repair/wiring source is currently available. These integrations remain explicitly unavailable; no external messages or charges were initiated.

## Subsequent deployment split

For the current three independent apps and centralized backend, use [THREE_APP_DEPLOYMENT.md](THREE_APP_DEPLOYMENT.md). Earlier combined-window run recipes above are retained as historical/compatibility instructions. The business workflow limitations still apply.
