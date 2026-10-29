# Admin Mode

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

PARTIALLY IMPLEMENTED overall. Authenticated ADMIN APIs provide current SQL
aggregate counts, account listing/status/role changes, business verification and
activation, listing moderation and audit events. Self-demotion/suspension rejected;
role/status changes revoke target tokens. Admin has no private diagnostic bypass.
First admin is explicitly bootstrapped locally after account registration.

Statistics currently count accounts, owned vehicles, centers, merchants, products,
scoped diagnostic sessions, monitoring runs and in-app notifications. Full active
user/engine/DTC/provider-delivery/operational analytics, support-case authorization,
feature flag administration and production update distribution are PLANNED.
Native admin browser can read real aggregates/accounts/audit; mutation UI pending.
