# Current vs target — pre-implementation audit

Baseline: 082b71d, 2026-10-29. Existing Python/FastAPI, PySide6, Compose and
SwiftUI project; do not rewrite its UI, diagnostic rules, icons, OBD or unit system.

| Domain | Current | Target / decision |
|---|---|---|
| Identity | Durable scrypt login, revocation, opt-in v2 | EXTEND settings, administrative governance; provider verification BLOCKED |
| Ownership | Many vehicles per account; canonical legacy profile table | KEEP; extend authenticated diagnostics |
| Consent | Per-vehicle, expiring/revocable profile/report/live read | EXTEND explicit diagnostic and maintenance scopes; no implicit write |
| Diagnostics | Shared DiagnosticSession/AI, legacy anonymous local API | REUSE engine through durable authorized session facade; preserve local mode |
| Workshop | Registration and owner membership, sharing invitations | EXTEND staff acceptance, work orders, scoped dashboard and verified directory |
| Monitoring | No durable owner schedules/dispatch | NEW durable schedules and deferred run records; gateway integration BLOCKED |
| Notifications | No delivery provider | NEW durable in-app records/preferences; external delivery BLOCKED |
| Marketplace | No durable merchant products/offers | NEW moderated products, stock, fitment claims, server discount quoting; payments FUTURE |
| Admin | Role exists, no business API | NEW audited governance and aggregate statistics; no private diagnostic bypass |
| Native business UI | Existing native legacy diagnostics, no login/workspace | EXTEND incrementally; mark unconnected screens PARTIAL, never claim API-only work is full parity |
| Repair/wiring | No licensed provider | NEW curated reference registry; external licensed content BLOCKED, no generated diagrams |
| Settings | EN/HY/RU + EU/US existing native settings | EXTEND account-level FR preferences and engineering conversions; full native FR translation remains separate |
| Updates | Existing platform-specific code | KEEP; signed distribution/store configuration not assumed verified |

Plan: additive migration, auth/object/consent services, reusable diagnostics,
workshop and market/admin workflows, monitoring lifecycle, tests, actual-state docs
and interactive graph. No deletion, CI/CD, new C++ production dependency or payment gateway.
