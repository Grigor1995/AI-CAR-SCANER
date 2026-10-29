# Optimization Decision Log

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

- KEEP existing APIs/UI/icons/localization/RBAC; no schema changes.
- REJECT separately sorting unsorted channel groups: paired 50k p50 regressed ~28.8%.
- ACCEPT reuse global stable order and one filtered per-channel list for stats/events.
  Exact arithmetic and event thresholds retained. Pair evidence reports 11.48%,
  13.55%, 20.49% p50 reductions at 1k/10k/50k respectively on this host.
- KEEP statistics.mean: fmean/native differ in general numerical/nonfinite behavior;
  no broad telemetry contract change justified by this audit.
- DO NOT INTEGRATE C++: faster than exact averaging but fmean is simpler and faster
  than C++ including packing in the experiment; no validated cross-platform benefit.
- DEFER model inference/physical OBD/production DB/concurrency/device graphics
  until actual environments/workloads available. Do not infer delays from CPU tests.
- Preserve rejected evidence and limitations so improvement claims are reviewable.
