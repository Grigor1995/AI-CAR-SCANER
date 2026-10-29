# Current Business Logic

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Before this change: durable accounts/passwords/revocable sessions; exactly
USER/CUSTOMER/ADMIN primary modes with MARKET portal role; owner-scoped canonical
vehicle profiles; workshop owner registration; accepted per-vehicle expiring
read consents. Feature opt-in, local legacy clients default unchanged.
Legacy diagnostic engine, OBD and native visual design already work independently.
No durable scoped diagnostic records/work orders/products/quotes/monitoring runs.
After this increment, see FINAL_BUSINESS_MIGRATION_REPORT for implemented backend
workflows and explicit incomplete native/provider functionality.

KEEP: diagnostic models, rules, evidence, hypothesis/test recalculation, local
AI adapters, transport safety, unit/theme/icon assets, build/update mechanisms.
EXTEND: ecosystem schemas/services/API and native application menu.
NEW: 12 additive workflow tables; business account browsers and interactive report.
DEFER: licensed providers, hardware gateway, full business mutation UI, payments.
