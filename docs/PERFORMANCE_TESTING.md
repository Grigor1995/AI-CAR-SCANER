# Performance testing

Baseline deterministic golden fixture: 10 warm-up + 100 timed runs, p50 0.57 ms,
p95 0.85 ms, min 0.43 ms and max 1.16 ms. Includes model copying and local
analysis; excludes physical OBD, network, LLM, UI startup and platform packaging.
This supports retaining the current Python engine, not a universal field SLA.

Measure startup, UI navigation, per-PID wire latency, decoding, incremental
analysis, DB query latency, auth hashing, memory and background CPU separately.
Do not include password hashing in the diagnostic 90 ms budget. Load tests need
concurrent clients, realistic ownership/grant sizes and PostgreSQL, not just a
single SQLite fixture. No new background polling is started by foundation.

For future C++ work, capture flamegraphs and resource pressure first, isolate a
hot path behind current interfaces, benchmark parity and regression golden
outputs, and document JNI/Objective-C++/Python bindings. No C++ performance or
coverage is claimed now.
