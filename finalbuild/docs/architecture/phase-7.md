# Phase 7 — Production Security, Multi-Tenancy & Observability

## Architecture decision
Phase 7 hardens the platform around authenticated principals, RBAC, tenant isolation, rate limiting, security audit events, metrics and tracing while keeping the diagnostic domain vendor-neutral.

## Security boundary
Client → authentication → authorization/RBAC → tenant isolation → diagnostic API → domain engine.

The diagnostic engine remains independent from authentication infrastructure.

## Implemented foundation
- HMAC-signed JWT-compatible tokens for development/test use
- principal and organization claims
- role/permission matrix
- sliding-window rate limiter
- security audit event model
- tenant isolation guard
- metrics registry
- tracing/span abstraction

## Production migration requirements
The included token implementation is intentionally dependency-light for development. Production should use a managed identity provider or hardened JWT/OIDC library, asymmetric signing keys, key rotation, refresh-token policy, MFA where appropriate, secret storage, PostgreSQL RLS, and centralized audit retention.

## Alternatives considered
- Full microservice IAM: rejected for now; unnecessary operational complexity.
- Custom authentication database: retained only as a future option; OIDC is preferred for production identity.
- Vendor-specific telemetry SDK: avoided; OpenTelemetry-compatible integration should sit behind these abstractions.

## Tests
Security and observability tests cover token verification, tampering rejection, RBAC, rate limiting, metrics and tracing.
