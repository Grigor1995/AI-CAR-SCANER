# Notification system — planned

No real email/SMS provider is connected in this milestone. Account contact
fields start unverified; they must not enable delivery or pretend verification.
Provider adapters, outbox/delivery tables and native preference screens belong
to Phase 2. Secrets remain process/local JSON ENV, not source or response bodies.

Contract: enqueue a consent-eligible notification with idempotency key, type,
severity, locale and verified destination reference; provider returns a delivery
identifier or explicit failure. An outbox transaction, retry/backoff, dedupe,
rate limit, quiet hours/cooldown and audit trail are required. A queued attempt
is not delivered. Fake provider tests are not external service integration.

Destination ownership verification, opt-out, deletion/retention and contact
redaction are release gates. No messages to external recipients are sent while
implementing this branch.
