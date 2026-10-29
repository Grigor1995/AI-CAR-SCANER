# Target architecture and present deployment

This is an incremental migration, not twelve deployed services. Desktop USER,
CUSTOMER and MARKET, Android flavors and iOS targets use the same authenticated
backend. Native Bluetooth/Wi-Fi/USB bridges stay close to hardware. Diagnostic
rules, inference decisions, ownership, consent and business writes remain backend-owned.

The first independently executable context is `vehicle-catalog`: immutable
catalog JSON and pure advisory protocol lookup, selected by an application port.
Its internal GET contracts need no cross-service SQL or customer data. Embedded
mode is the default to preserve local startup and latency; remote mode is an
explicit deployment choice. One process, own read model, internal credential,
readiness and timeout/failure tests make this a real optional service boundary.

Identity, diagnostics, telemetry, AI orchestration, workshop/customer workflows,
monitoring, notifications, marketplace and administration remain embedded. Their
shared transactions must be separated before independent deployments can be
claimed. Signed updates and purchase are future boundaries. Existing llama-server
is already an inference process; no duplicate native inference engine is introduced.
