# Service boundaries

| Context | Current implementation | Extraction gate |
|---|---|---|
| Identity | ecosystem/api.py, models.py, security.py; embedded SQL | Tenant/consent contracts and identity-only repository |
| Vehicle catalog | services/vehicle_catalog + vehicle/catalog_registry.py; optional separate process | Implemented for read-only catalog; profile ownership still embedded |
| Diagnostics / transport policy | diagnostic/, vehicle/, ecosystem/business_service.py | Isolate canonical diagnostic state transaction |
| Telemetry | telemetry/ and API; embedded in-memory | Bounded retention, tenant stream identity, durable stream contracts |
| AI | ai/; llama-server external inference | Keep decision orchestration near diagnostic context |
| Monitoring | ecosystem/business_service.py schedules; embedded | Real device executor and lease/idempotency semantics |
| Notifications | in-app records; embedded | Providers, consent, delivery outbox, retries |
| Customer | service centers, staff, work orders; embedded shared SQL | Scoped repositories replacing joins |
| Marketplace | merchant/product/offer; embedded shared SQL | Seller/verification read model and owned storage |
| Admin | embedded account permissions; no private diagnostic bypass | Audited administration contracts |
| Config | configuration/; embedded immutable manager | Authenticated control plane only if operationally justified |
| Updates | disabled | Signed manifest/key rotation and tested rollback |

The generated owner index deliberately labels mixed business composition as
`gateway` and other unmatched paths `UNASSIGNED`. Planned services with no source
files are not disguised as implemented services. Full vehicle accounts/history
have not moved into the public catalog context.
