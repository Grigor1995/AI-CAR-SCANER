# Phase 15 — Real Vehicle Data Acquisition

Phase 15 connects the Phase 14 telemetry intelligence layer to a reusable vehicle-data acquisition runtime.

## Responsibilities

- Adapter-agnostic acquisition lifecycle
- OBD-II PID polling
- CAN frame streaming
- UDS DID polling over the existing ISO-TP/UDS stack
- BLE/Wi-Fi/USB transport reuse
- reconnect with bounded exponential backoff
- bounded in-memory buffering
- durable offline queue when the delivery sink is unavailable
- sequence/timestamp provenance
- acquisition API status and record inspection

## Layering

```text
VCI / Transport
      |
      v
Protocol Client
OBD / CAN / ISO-TP / UDS
      |
      v
AcquisitionSource
      |
      v
AcquisitionManager
  |       |       |
  |       |       +--> OfflineQueue
  |       +----------> Record Buffer
  +------------------> Sink / Telemetry Service
      |
      v
Phase 14 Signal Intelligence
```

The acquisition manager does not own UI logic and does not assume a specific VCI vendor. The same interfaces can be hosted by Windows/Linux/macOS applications, Android phones/tablets, and the future custom Android diagnostic device.

## Physical transports

Existing Phase 2 transports remain the physical seams:

- BLE via `ObdBleTransport`
- TCP/Wi-Fi via `ObdWifiTransport`
- USB serial via `ObdUsbSerialTransport`

Phase 15 intentionally does not hard-code vendor-specific BLE UUIDs, TCP protocols, or proprietary device commands.

## Safety

This phase is read-oriented. No ECU programming, calibration writing, immobilizer operations, or other unsafe write workflows are added. UDS write/programming remains excluded from the MVP.

## Offline behavior

Records are first retained in a bounded memory buffer. If the configured delivery sink fails, records are serialized to JSONL through `OfflineQueue`. The queue is FIFO and supports `peek`/`ack`, allowing a later synchronization worker to deliver batches and acknowledge only successfully persisted records.

## Production follow-up

A production deployment should replace JSONL queueing with an encrypted device database, add backpressure/flow control, use monotonic sequence numbers persisted across restarts, and add transport-specific health metrics. Hardware-in-the-loop coverage should exercise unplug/replug, BLE reconnect, Wi-Fi loss, USB detach, adapter reboot, ECU communication timeout, and low-device-battery scenarios.

## Phase 14 integration

The backend simulator acquisition service now delivers numeric OBD records into the existing Phase 14 `TelemetryService`, preserving timestamps, PID names, sequence numbers, units, quality and source metadata. A future device-side sync worker can use the same record model and sink contract.
