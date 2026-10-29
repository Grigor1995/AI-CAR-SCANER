# Contracts

Catalog process: `python -m backend.services.vehicle_catalog --port 8011` from
`finalbuild`. Public `GET /health` is liveness only; `GET /ready` requires internal
bearer authorization and successfully loads owned read data. Internal protected
GET `/internal/v1/catalog/{stats,makes,models,fitments,profile}`. Inputs retain the
legacy length/year/limit constraints. Makes uses `query`, gateway uses legacy `q`.
Stats/profile return objects; makes/models/fitments arrays. Service OpenAPI is
available at `/openapi.json`; it describes internal read-only contracts only.

Gateway `/api/v2/ecosystem/catalog/{...}` uses the existing account bearer and
feature boundary. Profile image links are rebased to account-protected v2 portrait/photo
routes; legacy links/responses stay unchanged in legacy mode. `/api/v1/vehicle-registry/...` stays compatible in legacy mode.
Catalog-offline or invalid internal response → sanitized 503, never a success with
silent stale fallback. Missing model profile remains the legacy explicit 404.

ADMIN GET/PATCH `/api/v2/ecosystem/configuration`: read sanitized policy/defaults;
PATCH `{expected_revision: 1, changes: {"services.vehicle_catalog.retries": 2}}`.
Only timeout/retry reloadable fields are accepted; stale revision/restart-only
fields → 409. Durable audit precedes publication. Endpoint responses are no-store.
Changes are process-local runtime overrides, not a durable distributed config store;
restart returns to deployment JSON/ENV. No secret values are returned.
