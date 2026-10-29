# Dependency analysis before changes

Shared mutable state: legacy API sessions/persistence singleton and telemetry
in-memory lists. Identity and consent checks are DB-scoped per request; business
router/service modules mix account, vehicle, workshop and market models. The
foundation/business router import cycle is deferred at install time, not evidence
that Python executes an import-time cycle. The source index must label that scope.

Candidate: vehicle/catalog_registry.py reads immutable local JSON and imports
stdlib only. Its read facade can be independently deployed without SQL credentials.
Other vehicle/protocol orchestration remains local to diagnostics. The AI rule
engine is fast and in-process; model inference is already HTTP/native. Do not add
RPC to each microsecond PID/rule function. Source analysis must distinguish module
imports from runtime network calls and unresolved dynamic object calls.

Generated dependency/call graphs and SCC reports will be the reproducible evidence;
this audit does not fabricate a manually enumerated function catalog.
