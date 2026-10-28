# Feature matrix

Status key: EXISTING = baseline code; FOUNDATION = first branch milestone;
PLANNED = specified, not completed. Actual execution is in IMPLEMENTATION_REPORT.

| Capability | Backend | Desktop / Android / iOS |
|---|---|---|
| Vehicle catalog, VIN support, real/simulated OBD, live data | EXISTING | EXISTING; hardware/platform support varies |
| Symptoms, rules, AI/RAG, tests and recalculation | EXISTING | EXISTING native clients |
| Unicode PDF, profile reuse, neon assets/themes | EXISTING | EXISTING |
| Account register/login/logout, profile language/timezone | FOUNDATION | PLANNED login/profile screens |
| Three modes + MARKET portal authorization contract | FOUNDATION | PLANNED native selectors |
| Owned vehicles and consent-scoped workshop reads | FOUNDATION | PLANNED invitation/consent screens |
| Verified email/mobile, MFA/recovery | PLANNED | PLANNED; no verified-delivery claim |
| Daily scheduling, deferred device scans, alert delivery | PLANNED | PLANNED; OS restrictions apply |
| Licensed wiring/repair guides, work orders | PLANNED | PLANNED; provider/license required |
| Merchant catalog, stock, offers, compatibility | PLANNED | PLANNED |
| Production admin analytics/moderation | PLANNED | PLANNED; existing in-memory workshop stats are not substitutes |
| Shared high-performance C++ core | MEASUREMENT-GATED PROPOSAL | No C++ implementation at baseline |

Do not infer client feature parity for new foundation endpoints from existing
native diagnostic parity. Foundation does not claim a finished ecosystem.
