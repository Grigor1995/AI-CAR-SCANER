# Implementation Plan

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Delivered increment: safe additive SQL/permissions + authenticated shared
diagnostics, workshop orders/staff, moderated marketplace and server quotes,
admin governance, owner monitoring lifecycle/in-app notices, settings/conversions,
native account browsers, tests and actual-state documentation/dashboard.

Remaining work in dependency order:
1. Finish native mutation forms and authenticated diagnostic/transport binding using
   current screens, preserving local legacy operation until the complete switch.
2. Implement contact verification/recovery with real email/SMS providers and
   audit/abuse policies; add delivery outbox, quiet hours/dedup/retry semantics.
3. Integrate authorized local/native gateway executor and background schedule
   claiming, power limits, missed/failed recovery; validate physical hardware.
4. Staff/organization lifecycle (reactivation, role edits, booking), proper consent
   amendment UI and safe legacy owner/history import with explicit mapping.
5. Licensed reference/fitment feeds and image-upload storage/moderation.
6. Complete four-language UI/report/AI translations and settings parity.
7. Production Postgres concurrency/retention, distributed limiter, privacy/export/
   recovery, store/signing and iOS/Windows QA. Payments remain future only.

No stage above is silently marked complete because its API/model exists. Target
workflow definition of done still requires full native end-to-end integration.
