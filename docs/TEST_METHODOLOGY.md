# Test methodology

Run unit, API/integration, consent/tenant-negative, migration-preservation,
golden diagnostic, native contract and performance tests separately. Use real
execution evidence; do not add counts from overlapping selections. Target >=90%
coverage on suitable production core logic and critical authorization branches.

Use isolated SQLite + FastAPI TestClient for foundation; do not depend on a
developer's PostgreSQL. Verify additive migration with a pre-existing profile,
rollback preservation, server role checks, token lifecycle and no legacy bypass.
Mock external destinations only at provider boundaries and label them as fakes.

Desktop uses existing offscreen Qt suites; Android JVM/lint/build uses existing
Gradle project. Device instrumentation, real ELM sessions, iOS and Windows
release execution have independent gates. Baseline 966 Python passes and high
line coverage do not prove forthcoming email, marketplace or hardware behavior.
No CI/CD or external messaging/deployment is run.
