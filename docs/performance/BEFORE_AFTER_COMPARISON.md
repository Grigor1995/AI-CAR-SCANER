# Before After Comparison

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

| Samples | Before p50 / p95 / p99 ms | After p50 / p95 / p99 ms | p50 reduction | Python peak before / after KiB |
|---|---|---|---|---|
| 1000 | 1.761 / 2.247 / 2.987 | 1.559 / 2.123 / 5.392 | 11.48% | 35.1 / 35.1 |
| 10000 | 20.677 / 23.958 / 44.323 | 17.875 / 20.378 / 22.166 | 13.55% | 672.0 / 672.0 |
| 50000 | 186.619 / 240.184 / 245.491 | 148.372 / 190.236 / 234.004 | 20.49% | 3796.9 / 3796.9 |

Only shared backend telemetry preparation changed. No speedup is claimed for
untouched PID, diagnostic engine, API health, database, UI or LLM. Those unpaired
measurements may vary due to host scheduling/cache. Warm file-cache process import
is separate from GUI cold startup. The reduction is an entire telemetry summary
call, not entire vehicle diagnosis or hardware round-trip.
