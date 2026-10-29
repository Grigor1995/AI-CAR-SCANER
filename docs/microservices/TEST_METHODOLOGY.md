# Local test methodology

Configuration: schema/default parity, strict values/unknown fields/version, immutable
snapshots, ENV/preference precedence, secret-safe errors, runtime field restriction,
optimistic revision and audit-before-publish failure. Real SQL/account tests cover
ADMIN-only patch, unauthorized access and unchanged public account catalog gateway.

Catalog: health vs authenticated readiness, bad/missing internal credential, input
bounds, safe correlation IDs, real uvicorn subprocess HTTP equivalence for five
operations, stopped-process partial failure and sanitized 503. Fresh import asserts
catalog process has no SQLAlchemy/identity/session-persistence imports.

Source: AST stable IDs/line shifts/async/typed declarations/literal routes, native
parser extraction, unresolved receiver calls, referential integrity and redaction.
Chromium uses actual pointer events for pan/drag, wheel zoom, all views, filter,
source navigation, bounded graph, layout round-trip and invalid import. No CDN.

Regression: repository common pytest and existing five Desktop groups/coverage,
real SQLite+HTTP ecosystem smoke, Android three-flavor Kotlin/instrumentation
compilation/JVM/lint/APK build and identity/resource inspection. iOS/Windows/real
OBD/provider acceptance is explicitly BLOCKED when unavailable, not replaced by
syntax checks or emulator-hardware claims. See final report for measured results.
