# Phase 6 — Professional Platform

## Goal
Add multi-technician workshops, organizations, fleet management, RBAC, subscriptions, audit logging and operational analytics while preserving the offline diagnostic architecture.

## Architecture decision
Keep the diagnostic engine and vehicle protocol stack unchanged. Add a professional-platform domain around them.

Core boundaries:
- Identity / organization
- RBAC
- Fleet
- Subscription
- Audit
- Usage analytics
- Reporting

## RBAC
Roles: owner, admin, technician, viewer.

Diagnostic logic remains independent from authorization. Authorization controls who may invoke operations; it does not decide diagnostic conclusions.

## Offline
The device remains authoritative for locally created diagnostic evidence while offline. Synchronization must use stable IDs and idempotent operations. Conflicts should be resolved per aggregate, with append-only evidence/audit events preferred over destructive overwrites.

## Security
Production deployment must add real authentication, token validation, tenant isolation at the DB layer, secret management and rate limiting. The in-memory platform service is a development implementation only.

## Subscription
Subscription models are domain metadata only in this phase. No payment provider is coupled to the diagnostic core.

## Known limitations
- In-memory service for development.
- Authentication provider not selected.
- Billing provider not integrated.
- Usage aggregation is event-based reference logic.
- PostgreSQL schema is prepared but service persistence wiring is next hardening step.

## Next step
Security hardening, real identity integration, production persistence, observability, CI quality gates and end-to-end workshop workflows.
