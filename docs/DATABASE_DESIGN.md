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
