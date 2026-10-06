# Phase 20 — Active ECU Discovery & Network Topology Correlation

Phase 20 promotes passive network-discovery candidates through an explicit, safe, read-only active verification step.

## Goals
- Verify inferred UDS request/response pairs with active ReadDataByIdentifier requests.
- Preserve the distinction between observed, inferred, active responder, and confirmed ECU identity.
- Correlate confirmed responders with passive candidates and configured gateway routes.
- Avoid diagnostic write/programming/security-access operations.

## Active probe policy
Only service `0x22 ReadDataByIdentifier` is generated. The default allowlist is:
- `0xF190` VIN
- `0xF187` software version
- `0xF191` hardware version

The policy limits target count, timeout, and inter-probe delay. Production deployments should add adapter-specific rate/bus-load controls.

## Classification lifecycle
`OBSERVED_CAN_NODE` → `UDS_REQUEST_RESPONSE_INFERRED` → `ACTIVE_UDS_RESPONDER` → `CONFIRMED_UDS_ECU`

A timeout remains `NO_RESPONSE`. A negative UDS response proves that a responder exists but does not by itself confirm identity.

## Gateway correlation
When a configured `GatewayRoute` matches a passive candidate's request/response IDs and target bus, the active probe is sent on the route's source bus. A successful response is reported as a gateway-correlated verification event; it does not bypass the existing route configuration.

## Safety boundary
No `0x10` session switching, `0x11` reset, `0x14` clear-DTC, `0x27` security access, `0x2E` write-data, `0x31` routine control, `0x34`/`0x36`/`0x37` programming, coding, or flashing operations are exposed by Phase 20.
