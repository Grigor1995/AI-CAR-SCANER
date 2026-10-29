# Test Methodology

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Use real SQLite SQLAlchemy sessions and FastAPI HTTP, not mocks of permissions,
prices or ownership. Reuse the existing foundation fixture and test current roles,
wrong owner/tenant, read-vs-write, revoke/expiry, staff acceptance/disable, immutable
completed work orders, moderation, offers/stock/quantities, account suspension,
settings, deferred scans and French errors/navigation. Optimistic diagnostic saves
reject stale writers. Existing golden diagnostics, OBD and UI tests still run.

Critical business coverage target >=90%, measured with pytest-cov branch support.
Native Desktop boundary tests check transient credentials and navigation using
HTTP transport doubles; backend logic is separately real SQL/HTTP. Android local
Gradle builds and JVM tests compile actual Compose changes; instrumentation source
compilation is not a device test. iOS source inspection is not a build claim.
Subprocess smoke migrates a temp DB, uses real Uvicorn/socket HTTP and restarts to
check persistent diagnostics/preferences/tokens/consent. Browser QA uses Chromium
CDP with actual drag/wheel for bundled dashboard. External providers/hardware are
BLOCKED/NOT RUN; never label them PASS.
