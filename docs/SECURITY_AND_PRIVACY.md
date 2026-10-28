# Security and privacy

Baseline API routers were unauthenticated despite isolated role/token helpers.
Foundation must be opt-in, database-backed and fail closed: no legacy anonymous
route may bypass the new ownership boundary once ecosystem mode is enabled.
Default local operation remains compatible and must not be advertised as a
production public multi-tenant API.

New login design uses scrypt hashes and random opaque bearer sessions stored as
hashes, expiring/revocable server-side. Resolve roles, active account and staff
membership from the database on each request. Public registration cannot grant
ADMIN or MARKET. Explicit owner consent is read-scoped, vehicle-scoped,
time-limited and revocable; platform ADMIN does not imply private vehicle access.

Audit IDs/actions without passwords, bearer tokens or contact payloads. Use
HTTPS on shared deployments, trusted proxy configuration and least-privilege DB
credentials. In-process auth throttles are single-instance protection, not a
distributed production rate limiter. MFA, verification/recovery, TLS deployment,
retention/export/deletion, backup restore and security review remain gates.
SQLite integration is not a substitute for PostgreSQL concurrency isolation
and field security testing.

Foundation now uses a loopback runner bind by default. Scrypt's stored profile
is N=32768, r=8, p=3 with 16-byte random salt and a 32-byte digest; verification
rejects unsupported stored cost profiles. Password hashing is deliberately
separate from the diagnostic latency target. Login failures are audited without
recording the submitted email/password or raw token. Invitation acceptance uses
an atomic unaccepted-state update plus unique owner/center/profile constraints.
