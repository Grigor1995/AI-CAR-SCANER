# Performance Baseline

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

Baseline captured BEFORE application edits; machine-readable evidence:
[evidence/baseline.json](evidence/baseline.json), cProfile baseline.prof.
The first harness attempt failed because an empty DATABASE_URL was not a valid
SQLAlchemy URL. Harness was corrected to isolated sqlite memory before baseline
capture; no application optimization had been applied.

- diagnostic_analysis: p50 0.5951, p95 0.9602, p99 0.9919 ms; 1506.5 ops/s; Python peak 52217 bytes.
- pid_snapshot: p50 0.0242, p95 0.0580, p99 0.1399 ms; 32962.6 ops/s; Python peak 2303 bytes.
- dtc_decode: p50 0.0017, p95 0.0038, p99 0.0288 ms; 317551.1 ops/s; Python peak 464 bytes.
- session_json: p50 0.0047, p95 0.0078, p99 0.0921 ms; 120237.6 ops/s; Python peak 1426 bytes.
- telemetry_summary_1000: p50 1.8905, p95 3.2030, p99 3.8595 ms; 462.9 ops/s; Python peak 35956 bytes.
- telemetry_summary_10000: p50 21.6640, p95 31.7621, p99 33.2105 ms; 43.9 ops/s; Python peak 688168 bytes.
- telemetry_summary_50000: p50 189.2053, p95 223.1554, p99 233.7583 ms; 5.3 ops/s; Python peak 3888072 bytes.
- http_health_inprocess: p50 2.3438, p95 2.7453, p99 3.4520 ms; 418.1 ops/s; Python peak 71287 bytes.
- sqlite_indexed_history_100: p50 0.0294, p95 0.0890, p99 0.3485 ms; 23400.6 ops/s; Python peak 4499 bytes.

Backend fresh-process import observations ms: [746.929736007587, 713.5045369941508, 793.1246000080137, 706.8880839942722, 695.1823029958177]. OS page cache was warm; NOT a cold boot.

Per-case process CPU time, single-core CPU utilization, traced Python peak and GC
counts are recorded. RSS/native allocations, full GUI cold startup, Windows EXE,
physical adapter connect/detection/ECU/polling timeouts, socket concurrency, live
PostgreSQL, RAG corpus/model prediction, LLM tokens/s and GPU frames: NOT MEASURED.
No zeroes or extrapolated figures replace unavailable results.

Desktop current offscreen source measurement: window construction 419.381 ms; navigation p50 2.322 / p95 12.622 ms over 70 changes; Qt timer p95 0.214 ms; Python allocation peak 2614.15 KiB. These were captured after the telemetry change and have no comparable before measurement, so no UI improvement claim. See evidence/desktop-offscreen.json.
