# Phase 2 — Generic OBD

## Architecture decision
Phase 2 adds a vendor-neutral OBD-II transport and protocol layer. The transport is separated from ELM327 command parsing and from the diagnostic session domain.

`DiagnosticSession -> Device/Adapter -> DiagnosticTransport -> OBD protocol -> Vehicle`

Supported transport seams:
- BLE/GATT (configurable UUIDs)
- Wi-Fi/TCP
- USB/serial
- simulator transport for CI

## Why
A real VCI should be replaceable without changing diagnostic reasoning. Mobile devices own their platform-specific radio/USB lifecycle; the shared domain consumes normalized vehicle evidence.

## Alternatives considered
- Direct vendor SDK dependency: rejected for core path because it couples the product to one VCI.
- Implementing OBD logic inside Flutter: rejected because Desktop and future Android hardware would duplicate protocol behavior.
- Full CAN/UDS stack now: deferred to Phase 3.

## Phase 2 scope
- ELM327-style initialization
- VIN (Mode 09 PID 02)
- generic DTC reading (Mode 03)
- standard live PIDs: RPM, coolant, speed, throttle
- BLE/Wi-Fi/USB transport abstractions
- simulator-backed OBD tests

## Safety boundary
Only generic read/diagnostic operations are implemented. No ECU coding, flashing, actuator writes, security access, or programming.

## Known limitations
- ELM327 command support varies by adapter.
- BLE service/characteristic UUIDs are device-specific and must be configured.
- Wi-Fi assumes a TCP OBD endpoint; vendor-specific discovery is intentionally outside the core.
- USB uses serial adapters where the OS exposes a serial device.
- OEM-specific DTC/PID semantics are deferred.

## Next step
Phase 3 adds CAN, ISO-TP, and UDS as independent protocol modules above the same transport/adapter abstractions.
