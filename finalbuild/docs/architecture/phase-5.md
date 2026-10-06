# Phase 5 — Custom Android Diagnostic Device

## Architecture decision
Treat the custom Android diagnostic tablet/device as a productized client around the existing vendor-neutral diagnostic stack. The device owns UI, connectivity, offline persistence, sync, device health and OTA lifecycle; diagnostic reasoning remains shared with the platform.

## Layers

```text
Android Application
├── Diagnostic UI
├── Session Coordinator
├── Device Manager
├── Connection Manager
├── Local SQLite/Drift DB
├── Sync Queue
├── Offline Rules/ML/AI
├── Health Monitor
└── OTA Manager
        |
     Device SDK
        |
   Custom VCI Transport
        |
    CAN / OBD / future ISO-TP
```

## Offline-first rules
No diagnostic evidence is lost when the network disappears. Writes are persisted locally and represented as idempotent sync operations. The backend is authoritative only after synchronization; conflict handling must preserve the diagnostic audit trail.

## OTA safety
Phase 5 implements manifest validation and policy only. Production OTA must add signature verification, rollback slots, staged rollout, power/thermal checks and recovery mode before field deployment.

## Custom VCI
`CustomVciCodec` is an application/device framing layer, not a replacement for CAN, ISO-TP or UDS. Vehicle protocols remain below this boundary.

## Alternatives
- Native Android Room/DataStore instead of Flutter Drift: better direct Android integration, but duplicates mobile data code.
- Android AIDL service boundary: useful for isolated privileged VCI services, but adds IPC complexity.
- Cloud-only sessions: rejected for workshop/offline requirements.

## Known limitations
- No physical custom Android hardware is included.
- No production OTA signing/rollback implementation.
- No privileged USB driver.
- Offline local LLM/ML runtime is an interface/foundation, not a bundled model.
