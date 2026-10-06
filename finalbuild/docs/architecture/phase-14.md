# Phase 14 — Real-Time Vehicle Telemetry & Signal Intelligence

## Goal

Turn raw live vehicle samples into synchronized signal statistics, events, and measured diagnostic evidence without allowing analytics to claim a root cause by itself.

## Flow

OBD/CAN adapter -> telemetry samples -> stream service -> per-signal analytics -> events -> measured evidence -> DiagnosticSession -> reasoning/test planner.

## Data model

`TelemetrySample` stores session, timestamp, PID, value, unit, source, sequence and quality. `SignalStats` captures min/max/mean/stddev/slope/rate. `SignalEvent` records signal behavior with provenance metadata.

## Detection

The MVP uses deterministic plausibility and change-rate thresholds. These are configurable signal definitions, not manufacturer-specific diagnoses. A detected event becomes `VEHICLE_MEASURED` evidence and is re-evaluated by the diagnostic engine.

## Persistence

The production PostgreSQL schema adds `telemetry_samples` and `telemetry_events` with session/PID/time indexes. The runtime service remains in-memory until the persistence adapter is wired in, preserving the offline-first boundary.

## Safety

Signal events are evidence, not component confirmations. No automatic ECU writes, programming, actuation, or unsafe commands are issued by telemetry analysis.

## Next integration

Phase 15 should connect this telemetry stream to real OBD PID acquisition, CAN/ISO-TP/UDS adapters, buffering/backpressure, time synchronization, reconnect handling, and time-series persistence.
