# Next development stages

1. Replace mixed business API direct SQL with context repositories and typed
   consent-aware DTOs, keeping real workflow regression tests.
2. Extract notification outbox/inbox after choosing real delivery providers and
   defining verification consent/rate limits. Never simulate successful delivery.
3. Introduce device execution leases and bounded telemetry retention; migrate
   transport-specific settings into a shared backend OBD policy contract.
4. Incrementally improve index semantic resolution using actual Kotlin/Swift
   compiler metadata and C++ compilation database when those toolchains exist.
   Add precise receiver/type evidence before claiming verified native call edges.
5. Validate Windows PyInstaller/installer and macOS Xcode/iOS devices; physical
   OBD pairing/VIN/PID sessions remain hardware acceptance gates.
6. Signed updates/payment capabilities stay disabled until their safety, provider,
   legal and regression gates are implemented. No CI/CD is part of this plan.
