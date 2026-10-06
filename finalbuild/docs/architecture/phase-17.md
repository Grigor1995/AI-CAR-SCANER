# Phase 17 — Multi-ECU Vehicle Network & Gateway Diagnostics

## Scope

Phase 17 extends the read-only CAN/ISO-TP/UDS runtime from one ECU to multiple ECUs sharing a vehicle network.

### Design goals

- one `DiagnosticSession` can contain many ECU nodes
- one CAN receive loop demultiplexes frames to ECU-specific protocol channels
- UDS requests can run concurrently without response cross-talk
- topology keeps ECU and gateway metadata separate from protocol logic
- cross-ECU DTC correlations remain evidence, not confirmed root cause
- physical gateway routing remains an adapter/runtime concern; simulator routes are logical topology metadata
- no ECU coding, flashing, security access, immobilizer operations or DTC clearing are added

## Runtime

```text
                         DiagnosticSession
                                |
                      VehicleNetworkTopology
                     /          |            \
                  ECU-A      Gateway      ECU-B
                    |           |            |
                 7E0/7E8     CAN0↔CAN1    7E1/7E9
                    \           |            /
                     +------ CAN Demux -----+
                                |
                          ISO-TP / UDS
                                |
                           Protocol Trace
```

`CanBusDemultiplexer` owns the single underlying receive loop and routes by CAN arbitration ID into `RoutedCanChannel` queues. This is required for safe concurrent UDS reads on a shared bus.

## APIs

- `POST /api/v1/multi-ecu/sessions/{session_id}/connect`
- `POST /api/v1/multi-ecu/sessions/{session_id}/disconnect`
- `GET /api/v1/multi-ecu/sessions/{session_id}/topology`
- `POST /api/v1/multi-ecu/sessions/{session_id}/identify-all`
- `POST /api/v1/multi-ecu/sessions/{session_id}/dtcs/read-all`
- `GET /api/v1/multi-ecu/sessions/{session_id}/trace`

## Cross-ECU correlation

The runtime groups identical DTCs reported by more than one ECU and marks `Uxxx` codes as network-related candidates. These are diagnostic signals only; the reasoning engine must continue to validate power, CAN integrity, gateway paths and ECU-specific evidence before confirming a root cause.

## Production limitations

The current HTTP path uses deterministic ECU simulators. Real gateway routing, DoIP, CAN-FD transport policies, OEM addressing databases, security access and hardware-specific bus/channel selection remain device-side adapters and later phases.
