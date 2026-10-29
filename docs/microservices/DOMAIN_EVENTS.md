# Domain events

No broker or fake producer/consumer is introduced. The first extraction only
serves idempotent reads and has no business mutations requiring domain events.
Current persisted audit entries are not advertised as a reliable event bus.

Future notifications/marketplace extraction should use a transactional outbox in
the owning SQL transaction. Proposed envelope: event_id, type, schema_version,
occurred_at, producer, aggregate_id, correlation_id, payload. Consumers keep an
idempotency inbox, acknowledge only durable effects, use bounded exponential
retry/dead-letter handling and retain replay/audit metadata. Examples for future
contract review: DiagnosticTestRecorded.v1, ConsentRevoked.v1, MerchantVerified.v1.
These are proposed, not emitted today. Exclude VINs, bearer tokens and private
notes from general broadcast events; consent revocation must gate reads immediately.
