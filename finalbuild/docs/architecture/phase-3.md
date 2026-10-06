# Phase 3 — CAN / ISO-TP / UDS

## Architecture decision
Implement CAN, ISO-TP and UDS as independent protocol layers over an abstract `CanBus`. The diagnostic domain does not depend on a particular VCI.

## Why
- Protocols can be tested without a vehicle.
- Future J2534/vendor/custom adapters can provide the same CAN abstraction.
- UDS remains separate from transport and CAN framing.
- Unsafe ECU write/programming services are intentionally absent.

## Implemented
- `CanFrame` with arbitration ID, DLC, timestamp, classic CAN/CAN-FD metadata.
- `CanBus` abstraction.
- ISO-TP single-frame and multi-frame transmit/receive, flow control, sequence validation, timeout/error handling.
- UDS request/positive/negative response handling.
- Read-oriented UDS services: DiagnosticSessionControl, ECUReset, ReadDataByIdentifier, ReadDTCInformation.
- Deterministic simulated CAN bus and protocol tests.

## Trade-offs
The Phase 3 stack targets classic ISO-TP/UDS first and keeps CAN-FD as metadata/abstraction. OEM-specific addressing, timing profiles and security access are deferred.

## Known limitations
- No ECU flashing/coding/programming.
- No SecurityAccess implementation.
- No OEM-specific DID database.
- Simulator is intentionally small and deterministic.

## Tests
`pytest tests/vehicle/can tests/vehicle/isotp tests/vehicle/uds`
