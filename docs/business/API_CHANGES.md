# Api Changes

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Existing foundation /api/v2/ecosystem remains opt-in. New domains below that
prefix: settings, diagnostics/analyze/tests/obd-plan/live/history; staff invitations;
work orders; verified directory; merchants/products/offers/quotes; monitoring/runs;
notifications/read; admin governance/references/audit; authorized navigation.
No active payments/orders checkout API. Primary /workspace remains USER/CUSTOMER/ADMIN;
/navigation accepts MARKET as explicitly non-primary portal.

New mutation bodies forbid extras and constrain IDs/enums/numeric limits/dates.
Typed responses cover settings, diagnostic sessions, products, quotes, work orders,
schedules/runs/navigation. Remaining business dictionary responses are narrowly
constructed, not raw ORM serialization. Bearer required except registration/login.
Errors are stable codes + EN/HY/RU/FR, invalid fields exclude passwords, no-store.
UI bearer is memory-only and bound to configured endpoint. Redirects disabled in
new clients. Account deletion/data export, distributed throttling and production
retention/pagination remain release work. OpenAPI is available from the running
backend /docs and /openapi.json; saved contract: ../architecture/ecosystem-openapi.json.
