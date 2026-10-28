# Database design and migration strategy

Baseline has PostgreSQL bootstrap `infrastructure/postgres/schema.sql`, JSON
DiagnosticSession persistence and `vehicle_profiles` payload storage; Alembic
was a dependency without checked-in revisions. New foundation migration setup
is additive. Production target PostgreSQL; SQLite exercises portable contracts.

| Table | Foundation purpose / key relations |
|---|---|
| ecosystem_accounts | UUID identity, normalized unique email, scrypt hash, profile, language/timezone, active and unverified-contact flags |
| ecosystem_account_roles | account FK + constrained USER/CUSTOMER/ADMIN/MARKET role; composite primary key |
| ecosystem_auth_sessions | hashed random token, account FK, expiry/revocation; no raw bearer token |
| ecosystem_service_centers | UUID business, name/address/contact fields, verification false |
| ecosystem_staff | center/account FKs, constrained existing staff role, active; composite primary key |
| ecosystem_vehicle_ownership | account/profile FKs, unique profile owner; references existing vehicle_profiles |
| ecosystem_invitations | center + invited-account FK, expiry and acceptance; no access before owner action |
| ecosystem_access_consents | owner/center/profile FKs, scopes, expiry/revocation; unique sharing relationship |
| ecosystem_audit_events | actor, action, target and UTC timestamp; no plaintext password/token/contact payload |

No existing users/organizations are silently promoted or equated with the new
account identities. The legacy profile table may be created if absent with its
existing two-column schema; an existing profile row is not reassigned. Remaining
schedule/outbox, repair/market and measurement-owner relational extensions are
planned. No fake empty production tables for those unimplemented features.

Run Alembic explicitly with DATABASE_URL; feature enablement is not a migration.
Backup first; verify legacy row retention and foreign keys, test upgrade twice
through version tracking, and downgrade only after a rollback/retention decision.
Keep legacy vehicle_profiles on downgrade. PostgreSQL live migration execution,
concurrent rollout and backup restoration require deployment integration tests.

Alembic autogeneration is explicitly restricted to `ecosystem_*` tables, so
unrelated legacy tables are not proposed for removal. Invitation acceptance
claims an unaccepted, unexpired invitation atomically; PostgreSQL concurrency
execution remains a release gate even though SQLite/API behavior is covered.


## Target schema extensions (proposed, not created by revision 0001)

| Product entities | Reuse / future extension |
|---|---|
| legacy users/organizations, accounts and user profiles | keep legacy rows; explicit identity mapping before any import, no automatic ownership |
| catalog vehicles, owned vehicle profiles | catalog stays shared reference data; ownership belongs to profile links, not every catalog model row |
| devices, sessions, measurements, DTCs, hypotheses, tests/results | reuse existing DiagnosticSession and device models; next milestone adds owner/session/device ACL links before exposing v2 diagnostics |
| maintenance records and work orders | future CUSTOMER transaction/history tables, scoped by owner consent and staff membership |
| schedules, scan runs and alert rules | Phase 2 normalized schedule/run state, timezone and availability reasons; no pretend completed scans |
| notifications and deliveries | transactional outbox, destination verification, retry/dedupe/cooldown and retention records |
| repair guides/references | licensed source/version/fitment metadata and access rights, not generated OEM facts |
| merchants, products and compatibility | merchant approval, exact stock/price/currency and verified fitment source references |
| offers and discount eligibility | server-side audience/expiry/quantity constraints separate from diagnostic ranking |
| audit and operations | new foundation audit is real; future retention, admin review, export/delete and backup policies need dedicated implementation |

Future schema normalization must preserve existing evidence/test IDs and history.
Do not make one global device manager or anonymous session cache a tenant ACL.
