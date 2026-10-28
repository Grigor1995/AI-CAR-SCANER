# Development plan

Phase 0 audit and first Phase 1 milestone are the scope of this branch. Effort
ranges below are planning estimates for a small experienced team, not deadlines.

| Phase / milestone | Scope and source | Dependencies / migration | Acceptance / tests | Risk / effort |
|---|---|---|---|---|
| 0 audit + baseline | inventory, current UI/API/schema review, local interactive architecture | existing tests/toolchains | real baseline, measured p95, honest platform gaps | incomplete hardware evidence; 2–4 days |
| 1A foundation | ecosystem account/session/RBAC, owned profiles, workshop invitation/consent APIs | additive Alembic; reuse Vehicle, staff Role | owner isolation, revoked access, token expiry, migration preservation, >=90% suitable new logic | legacy bypass; 4–8 days |
| 1B authenticated diagnostics | scoped session/device/report adapters, operator role provisioning, offline identity mapping | 1A; explicit legacy ownership mapping | cross-tenant denial on every route; default local compatibility | broad existing API surface; 1–2 weeks |
| 1C native workspaces | current Desktop/Android/iOS login + allowed-mode selector + consent screens, localization | 1A/B API contract | EN/HY/RU and visual parity; token secure storage | Xcode/OS secrets storage; 1–2 weeks |
| 2A USER monitoring | schedule/timezone/quiet-hours + eligible gateway jobs, deferred scans | identity + device availability; schedule/run/outbox migrations | no OFF-ignition fake success, idempotent runs, DST tests | OS/battery limits; 1–2 weeks |
| 2B delivery/service discovery | provider interfaces, verified email/mobile, retry/dedupe, location consent | configured providers and contracts; delivery tables | fake provider tests separate from sandbox delivery; cooldown/privacy tests | paid services/geolocation; 1–2 weeks |
| 3 CUSTOMER | work orders, safe test methodology, licensed diagrams/repair docs | tenant/consent foundation + licensed data | approved-data-only access, real provenance, repair verification | OEM licensing; 2–4 weeks |
| 4 MARKET | merchant approval, products, compatibility, stock/discounts, offers | staff/admin controls; market migrations | unknown compatibility explicit, eligibility server-side, sponsored separation | catalog quality; 2–4 weeks |
| 5 ADMIN | protected role/configuration, real aggregates and audit, privileged MFA | auth/market/activity events | no fabricated stats, least-privilege admin, audited sensitive access | security posture; 1–3 weeks |
| 6 platform/performance | authenticated parity, eligible offline sync, measured hot-path tuning | native environments, hardware, conflict policy | real ELM evidence separate from simulations; C++ only if measured | platform gaps; 2–4 weeks |
| 7 production release | rate-limit store, backup/restore, retention/export/delete, pentest, signed release | all external/hardware gates satisfied | regression + permission + restoration + release acceptance | integration risk; 2–4 weeks |

Each milestone needs buildable code, meaningful tests, migration notes, current
UI/icon reuse and an updated implementation report. No automatic deployment or
CI/CD is introduced. A phase's UI screens/migrations are not complete until its
own acceptance gates pass. Keep incomplete functionality feature-gated.
