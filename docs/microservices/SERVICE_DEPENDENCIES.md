# Dependencies

`api/vehicle_registry_routes.py` → `services/vehicle_catalog/port.py` → either
pure `vehicle/catalog_registry.py` or authenticated HTTP → catalog process → its
immutable JSON read model and protocol hint functions. The separate catalog imports
no identity/session persistence or SQLAlchemy engine (fresh-process test).

The v2 gateway authenticates the existing bearer account before invoking catalog
reads. Legacy read contracts retain their paths/signatures but the ecosystem
legacy-block middleware is unchanged. Config administration depends on existing
ADMIN role and durable AuditEvent. No new role can bypass ownership or consent.

`docs/architecture/data/dependencies.json` contains file import evidence, scope,
source line and resolution. `summary.json` lists strongly connected components.
Deferred function imports are identified and are not labeled startup deadlocks.
Code imports are not network requests. Runtime monkey-patching, package __path__
aliases and native overloads limit static resolution; see SOURCE_CODE_INDEXING.
