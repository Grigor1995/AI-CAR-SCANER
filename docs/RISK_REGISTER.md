# Risk register

| Risk | Severity | Control / remaining gate |
|---|---|---|
| Legacy anonymous API bypasses accounts | Critical | Block legacy API paths when ecosystem enabled; native migration before rollout |
| Workshop/admin role confusion | Critical | Separate account modes and scoped staff roles; no ADMIN data bypass |
| Owner inferred from legacy anonymous rows | Critical | No implicit claims; explicit ownership mapping migration later |
| Concurrent consent revoke/read or invite accept | High | DB-backed checks, transactions/uniqueness; PostgreSQL race tests still required |
| Public signup/verification abuse | High | Bounded validation/throttles; verified contacts/MFA/recovery later |
| Unknown or fabricated vehicle/repair facts | High | Existing provenance/capability checks; licensed references and UNKNOWN states |
| Mobile unattended scan limitations / battery drain | High | No scheduler until eligible gateway, consent and availability model |
| Marketplace paid ranking contamination | High | Separate offers/eligibility from diagnostic evidence ranking |
| C++ rewrite destabilizes working clients | Medium | Measured optimization gate, preserve interfaces and golden regression |
| Platform validation unavailable | High | Label iOS/Windows/hardware BLOCKED or NOT EXECUTED, never PASS |
| SQLite tests conceal PostgreSQL concurrency | High | Production DB smoke/concurrency/backup gate |
| Huge source installer / provider downloads | Medium | Existing verified source/model handling; measure separately from diagnostic latency |

Also found: malformed nested vehicle input on the legacy session creation route
can escape manual validation. V2 typed input rejects this safely; legacy error
normalization remains in milestone 1B before exposing authenticated diagnostics.
