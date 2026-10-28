# API specification — foundation contract

Existing `/api/v1` diagnostic routes remain unchanged in local mode. Planned
foundation router prefix: `/api/v2/ecosystem`, enabled only with
`AI_CAR_ECOSYSTEM_ENABLED=1` and an explicitly migrated database.

| Method / suffix | Authentication / action |
|---|---|
| POST /accounts | public, throttled; validated profile + password, USER role only |
| POST /auth/login | public, throttled; opaque expiring bearer token |
| POST /auth/logout | bearer; revoke current session |
| GET /me | bearer; profile, authorized primary modes and portal roles |
| PATCH /me | bearer; bounded profile/language/timezone update; no privilege fields |
| POST /workspace | bearer; validate permitted USER/CUSTOMER/ADMIN selection; MARKET rejected as mode |
| GET, POST /vehicles | bearer; only owned legacy-compatible vehicle profiles |
| POST /service-centers | bearer; create unverified business + CUSTOMER/owner membership |
| POST /service-centers/{id}/invitations | owner/admin staff in center; invite existing account, no access grant |
| GET /invitations | bearer; only invitations addressed to current account |
| POST /invitations/{id}/accept | addressed owner; choose owned profile + read scopes + bounded expiry |
| GET /consents | bearer; owner list |
| DELETE /consents/{id} | owner; immediate revocation |
| GET /service-centers/{id}/vehicles/{profile_id} | current staff + active vehicle:read grant |

401 invalid/expired/revoked bearer; 403 forbidden role/scope; 404 disabled feature,
unknown/foreign resource; 409 conflicting identity; 422 invalid input; 429 rate
limit; 503 database unavailable/unmigrated. Return stable error codes and EN/HY/RU
messages selected by Accept-Language; never echo passwords/tokens in errors.
OpenAPI is generated from actual route models. This document is an implementation
contract, not proof that native clients already consume it.
