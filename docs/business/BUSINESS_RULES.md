# Business Rules

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

- Public registration grants USER only; business registration may grant CUSTOMER
  or MARKET but never ADMIN, verification or consent to someone else’s data.
- MARKET is not accepted by the primary /workspace mode endpoint.
- Every account/role is read from SQL per request; disabled account/revoked token
  immediately loses access. Administrative role/status changes revoke sessions.
- Organization membership is explicit: staff invitation must be accepted by target.
- Owner scope cannot be inferred from an anonymous legacy profile. New owned
  profile IDs are created; legacy data needs operator-approved identity mapping.
- Current ownership, active staff/center, owner active, consent expiry/revoke and
  requested scope are checked at access time, including reports and work orders.
- Read consent never implies diagnostic:write or maintenance:write.
- Admin governance grants no private diagnostic read bypass.
- Only active verified merchants’ approved listed products are public. Product
  changes reset moderation. Fitment remains an unverified seller claim.
- Quotes use integer minor currency units, one best eligible offer, discount
  floor rounding, explicit quantity/time/coupon/center eligibility and no checkout.
- Monitoring requires owner consent; no connected authorized gateway means a
  DEFERRED/MISSED record, never fabricated readings or ECU writes.
- Existing completed tests feed the same engine and regenerate next recommendations.
  UNKNOWN maps to existing INCOMPLETE, never a failed measurement.
