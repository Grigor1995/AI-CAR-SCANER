# Final Performance Report

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

The existing project is preserved. Shared telemetry summary preparation is
optimized beneath all clients; no UI/icon/navigation/dependency/schema/permission
change. Main foundation merge was completed first at 540e00f.

| Samples | Before p50 / p95 / p99 ms | After p50 / p95 / p99 ms | p50 reduction | Python peak before / after KiB |
|---|---|---|---|---|
| 1000 | 1.761 / 2.247 / 2.987 | 1.559 / 2.123 / 5.392 | 11.48% | 35.1 / 35.1 |
| 10000 | 20.677 / 23.958 / 44.323 | 17.875 / 20.378 / 22.166 | 13.55% | 672.0 / 672.0 |
| 50000 | 186.619 / 240.184 / 245.491 | 148.372 / 190.236 / 234.004 | 20.49% | 3796.9 / 3796.9 |

Exact modified production files:
- finalbuild/backend/telemetry/analysis.py: separate private prepared calculations;
  existing public functions preserve sorting and quality semantics. Add private
  combined sorted-input helper for trusted service caller.
- finalbuild/backend/telemetry/service.py: call combined helper instead of preparing
  same already-sorted channel twice; display names, counters and timestamps unchanged.

Additional tooling fix: finalbuild/scripts/benchmark_desktop.py provides inert base_url metadata to its no-network API test double; the existing offline benchmark otherwise failed during page construction. No production UI changed.

Added supporting files: benchmark_pipeline.py (multi-subsystem baseline),
compare_telemetry.py (frozen reference paired comparison), benchmark_native_mean.py
(optional C++ experiment), experiments/native_mean (C ABI, contract test, CMake),
tests/performance/test_telemetry_equivalence.py (61 edge/random regression cases),
interactive dashboard and this 15-document report/evidence set. No production
native bindings, JNI or Objective-C++ introduced. Existing code not deleted.

C++ decision: prototype numeric equivalence only fixture/tolerance-level;
ctypes packing dominates call overhead and fmean beats it. Exact statistics.mean
retained. No production C++ migration qualifies acceptance. Synthetic summary
speedup is meaningful for long histories, not a claim of faster ECU response.

Known limits: no physical ECU/adapter, real model inference, deployed PostgreSQL,
mobile GPU, Windows packaging or iOS build executed. Scheduler/notifications and
merchant/admin workflows are incomplete. In-memory telemetry retention remains
unbounded; pagination/retention/incremental summaries are next design decisions.
See REGRESSION_TEST_REPORT.md for final executed results, not previous-run claims.

Local run from existing Windows Git Bash clone:

```bash
cd ~/Desktop/AI-CAR-SCANER/git
git pull --ff-only origin main
python runner.py setup --skip-android --skip-ai
python runner.py desktop --no-ai
```

For existing installed local AI: python runner.py desktop (uses configured model).
Do not enable AI_CAR_ECOSYSTEM_ENABLED for current native legacy clients; default
is off. To view report, open docs/architecture/performance_architecture_dashboard.html
in a local browser; all assets are bundled, no CDN. If browser blocks local files:
python -m http.server 8765 --bind 127.0.0.1 --directory docs then open
http://127.0.0.1:8765/architecture/performance_architecture_dashboard.html locally.

Android with running emulator: python runner.py android. Verify exact
runner options with --help; platform prerequisites remain unchanged.

Final executed validation: common suite 1062 passed / 2 skipped; Desktop all five groups PASS; Android Gradle PASS (67 tasks, 66 cached); Chromium 12 checks PASS; native ASan/UBSan contract PASS. See evidence/regression.json. Windows/iOS/physical hardware limitations remain as above.
