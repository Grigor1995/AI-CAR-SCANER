# Status

Implemented: audited baseline; validated global JSON/schema/overlays; immutable
snapshots; startup compatibility bridge; allowlisted admin runtime patch with audit;
optional independently executable read-only vehicle catalog and authenticated v2
adapter; correlation IDs; language-aware source index and offline explorer;
three generated product icons wired to Desktop/Android/iOS and installer shortcuts.

Still embedded: identity, private vehicle profiles, diagnostic state, telemetry,
AI decision logic, monitoring, in-app notification records, customer workflows,
marketplace and admin. Shared business SQL joins are still present. Monitoring
execution/delivery providers, signed auto-update runtime and payment processing
are not implemented. Native C++ core is experimental only. Config contains policy
fields whose consumers remain staged; GLOBAL_CONFIG_REFERENCE identifies them.

Independent platform packaging and hardware gates are reported separately in
REGRESSION_REPORT. Do not interpret syntax/index/browser success as iOS runtime,
Windows installer or real-car protocol certification.
