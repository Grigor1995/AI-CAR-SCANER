# Strategy

1. Preserve baseline and document coupled routes/data. Implement typed config and
   first read-only port without changing legacy response semantics.
2. Run embedded compatibility tests. Independently run catalog with a service
   credential; compare HTTP and embedded responses. Test missing credential and
   stopped service, timeout and malformed responses.
3. Opt into remote mode using deployment JSON/authorized ENV. Keep local embedded
   default. Roll back by restarting with `AI_CAR_CATALOG_MODE=embedded`; no database
   migration/backfill is needed for immutable read-only data.
4. Extract repositories from mixed business modules before moving another context.
   Use contract tests, explicit transaction ownership and consent-aware read models.
   Introduce outbox/inbox only when a real asynchronous mutation consumer exists.

No wholesale rewrite, UI replacement, active payments or unmeasured C++ migration.
No CI/CD workflow was added. Local verification remains the release mechanism.
