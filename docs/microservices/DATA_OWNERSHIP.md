# Data ownership

The extracted catalog owns the immutable version-controlled `finalbuild/data/
vehicle_catalog.json` and `vehicle_fitments.json` read model. The protocol registry
contains advisory standards, not VIN-level verification. No account or diagnostic
record is copied to the catalog process. Read-model publication currently ships
with the repository, not a fabricated catalog update event pipeline.

The main backend still owns one SQLAlchemy database: foundation accounts/tokens,
vehicle ownership/consents, canonical diagnostic JSON, work orders, marketplace,
monitoring and in-app notifications. Sharing the database is explicitly transitional.
The migration did not split these schemas into fake independently owned databases.

Next extraction requires per-context repositories and removal of direct joins,
a versioned read DTO for dependent contexts, backfill/dual-read comparison, a
bounded reconciliation window and a reversible cutover before physical data moves.
Do not let a service query another service's private tables. No destructive
migration or deletion of existing customer records occurs in this increment.
