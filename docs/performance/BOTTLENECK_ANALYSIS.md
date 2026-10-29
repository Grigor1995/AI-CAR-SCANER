# Bottleneck Analysis

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

cProfile at baseline: 50k shuffled samples, 4 channels; 794,673 calls in
~0.394 s under profiling (instrumented observation, not benchmark latency).
Telemetry summary called sorted 10 times; sorted cumulative ~0.208 s;
8 statistics.mean calls ~0.087 s. Timings overlap and must NOT be added.

Root causes: global sort followed by two repeated quality filters/sorts per
channel; exact-rational averaging traverses values and deltas. Filtering and
statistics share identical valid chronological samples. The sort contract is
(timestamp_ms, sequence or -1); zero/None tie semantics are intentionally retained.

Rejected experiment: sorting each unsorted channel separately produced a 28.8%
p50 regression at 50k in paired testing (see rejected-grouped-sort.json). Reverted.
Selected change preserves global stable sorting and reuses a single filtered
channel list for both consumers. No arithmetic, event thresholds or UUID policy
changes. Unbounded storage remains a memory scalability limitation; not solved
by changing parser language.

Python fmean and C++ mean experiments expose remaining averaging CPU cost; fmean
is faster than C++ including list-to-native copy. Neither is shipped because
exact rounding/nonfinite behavior has not been established for all accepted
telemetry floats. Existing statistics.mean is retained.
