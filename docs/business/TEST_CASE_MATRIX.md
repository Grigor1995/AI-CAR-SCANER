# Test Case Matrix

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

| Domain | Cases |
|---|---|
| Identity | registration/login/revoke; role escalation denied; disabled accounts; input secrets absent |
| Ownership | multi-vehicle foundation; foreign vehicle denied; admin private read denied |
| Consent | unaccepted invite denied; read never grants write; scoped access revoked immediately |
| Diagnostics | canonical hypotheses/recommendations; result recalculation; native nulls/provenance; restart persistence; optimistic lost-update rejection |
| Workshop | target staff acceptance, role limits, owner removal denied, work-order completion, grant removal clears dashboard |
| Marketplace | unverified/unmoderated hidden; ownership; update resets approval; integer quote, coupon/public/customer/stock; no checkout |
| Directory/reference | verified listings only; filters; exact vehicle fitment; admin-only licensed reference registration |
| Monitoring | explicit consent/default daily; future dispatch conflict; deferred/missed/idempotent run; notification read/private state |
| Settings | four-language preference/error/navigation; IANA validity; positive/finite accurate unit conversions |
| Migration | foundation/legacy preservation; schema upgrade/downgrade; PostgreSQL offline DDL |
| Native | Desktop account browser tests + full five groups; Android Kotlin/APK/lint/JVM; iOS NOT VERIFIED |

Raw executed results and coverage are in evidence/ and FINAL_BUSINESS_MIGRATION_REPORT.
Missing providers/hardware, complete native editing and actual autonomous scans
are NOT RUN/BLOCKED rather than represented by passing mocked end-to-end tests.
