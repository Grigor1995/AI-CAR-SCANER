# Phase 19 — Vehicle Network Discovery & Automatic ECU Mapping

Phase 19 introduces passive network discovery on top of the multi-bus/gateway stack.

## Scope

- Observe CAN traffic without transmitting discovery probes.
- Build per-bus arbitration-ID profiles.
- Measure frame frequency / median periodicity and payload/DLC variability.
- Infer likely UDS request/response ID pairs using configurable offsets.
- Emit ECU candidates with explicit confidence and provenance.
- Surface unpaired active CAN IDs as observed nodes rather than confirmed ECUs.
- Keep discovery read/passive by default.

## Critical distinction

Passive CAN traffic can reveal useful network structure, but it cannot by itself prove an ECU identity. Candidates are therefore labeled as inferred or observed and must be promoted to confirmed identity only by a successful active diagnostic operation.

## Runtime

```text
CAN RX stream
    |
    v
Observation Buffer
    |
    +--> CAN ID profiles
    |      - count
    |      - DLC
    |      - periodicity
    |      - sample payloads
    |
    +--> UDS pair inference
    |      - request/response IDs
    |      - confidence
    |
    +--> ECU candidates
           - inferred
           - observed
           - provenance
```

## Safety

No automatic diagnostic probing, SecurityAccess, coding, flashing, DTC clearing, or programming is exposed by this phase. OEM-specific addressing rules should be supplied as configuration before active discovery is enabled in a future phase.
