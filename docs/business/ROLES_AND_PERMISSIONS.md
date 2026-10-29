# Roles And Permissions

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

| Actor | Allowed | Never implicit |
|---|---|---|
| USER | own profiles, diagnostics, schedules, preferences, notifications, quotes | other owners’ vehicles |
| CUSTOMER | active membership plus exact per-vehicle consent; work orders by technician+ | owner-wide vehicle access or writes from read grants |
| ADMIN | audited accounts/roles/center/merchant/moderation, aggregate counts/audit | unrestricted private session contents |
| MARKET portal | owned active merchant products/inventory/offers | another shop or confirmed fitment |

Staff levels reuse existing owner/admin/technician/viewer RBAC. Owner invites
staff; target accepts. Viewer cannot mutate diagnostics/maintenance. Owner cannot
be removed with staff-disable endpoint. New scopes: history:read, diagnostic:write,
maintenance:read, maintenance:write alongside vehicle:read/report:read/live:read.
Each consent remains one selected vehicle and at most 90 days.
Operator bootstrap is explicit local CLI for the first existing active account:
python finalbuild/scripts/bootstrap_business_admin.py --email ADDRESS --grant-admin.
No public privilege bootstrap or password/token output.
