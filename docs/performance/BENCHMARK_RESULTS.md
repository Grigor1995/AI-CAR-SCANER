# Benchmark Results

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

| Samples | Before p50 / p95 / p99 ms | After p50 / p95 / p99 ms | p50 reduction | Python peak before / after KiB |
|---|---|---|---|---|
| 1000 | 1.761 / 2.247 / 2.987 | 1.559 / 2.123 / 5.392 | 11.48% | 35.1 / 35.1 |
| 10000 | 20.677 / 23.958 / 44.323 | 17.875 / 20.378 / 22.166 | 13.55% | 672.0 / 672.0 |
| 50000 | 186.619 / 240.184 / 245.491 | 148.372 / 190.236 / 234.004 | 20.49% | 3796.9 / 3796.9 |

Native 10k-sample whole summary, ms p50 (separate experiment):

- python_exact_mean: 18.056
- python_fmean_experiment: 11.000
- cpp_copy_included_experiment: 13.307

The native prepacked microbenchmark excludes conversion and is not an integrated
performance claim. Exact mean, fmean and native experiments are sequential,
not paired; interpret direction conservatively. Native is slower than simpler
fmean in this fixture after packing. Keep exact arithmetic production contract.
All raw trials, CPU and Python peak data are in evidence JSON; CPU/native memory
unmeasured values are explicitly labeled.
