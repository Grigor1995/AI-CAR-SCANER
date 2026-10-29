# Future purchase architecture — disabled

Exactly three client products remain USER, CUSTOMER and MARKET. No fourth checkout
app is created. Purchase, checkout, payments and subscriptions are hard-disabled in
the schema and runtime patch API. There are no payment credentials, provider calls,
payment UI actions, card storage or claimed PCI processing.

A future purchase context should own quote/order/reservation/payment-reference
state. Review price/currency/version server-side, require approved merchants and
products, preserve consent and tax rules, and use idempotency keys for checkout.
Inventory reservation needs expiry/concurrency semantics; never trust a client price.
Payment providers receive hosted checkout details, not raw card data through our
backend. Signed verified webhooks must deduplicate and reconcile state transitions.
Outbox/inbox, immutable receipts, refunds, disputes, audit and retention are release
gates. Provider/legal decisions and contract tests precede enabling any flag.
