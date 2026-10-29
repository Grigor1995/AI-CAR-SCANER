# Performance Test Methodology

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

Use the prepared Python environment with requirements-dev plus Desktop dependencies.
From repository root:

```bash
python finalbuild/scripts/benchmark_pipeline.py --output docs/performance/evidence/local-baseline.json
python finalbuild/scripts/compare_telemetry.py --baseline-ref 540e00f --output docs/performance/evidence/local-paired.json
```

Pipeline: seeded 429 shuffled samples, four channels, 10 Hz/channel; INVALID each
101st sample; 1k/10k/50k histories. Construction is outside timing. Five warmups,
30 trials, nearest-rank p95/p99, process CPU, traced single-call Python allocation
peak outside latency sampling. No stochastic diagnostic/LLM provider.
Paired comparison loads trusted baseline source from local Git 540e00f, checks
canonical outputs, alternates AB/BA order for 40 rounds with five warmups per
variant. Resource passes are separate ten-call runs. No concurrent load during
paired capture. p99 with 40 observations is max; it is not a stable tail estimate.

Unpaired runs fluctuated materially and are retained, not used as improvement
proof. Paired results are authoritative for changed function only. Benchmarks
measure CPU synthetic preparation, not car polling rate. Python GC counts are
observations, not measured collection pause duration. True cold boot, RSS,
production concurrency and native allocator counts remain NOT MEASURED.

Native experiment (optional Linux developer toolchain):

```bash
g++ -std=c++20 -O3 -fPIC -shared finalbuild/experiments/native_mean/mean.cpp -o /tmp/libmean.so
python finalbuild/scripts/benchmark_native_mean.py --library /tmp/libmean.so --output /tmp/native-results.json
g++ -std=c++20 -g -fsanitize=address,undefined -fno-omit-frame-pointer finalbuild/experiments/native_mean/{mean,test_mean}.cpp -o /tmp/test_mean
/tmp/test_mean
```

CMake alternative: cmake -S finalbuild/experiments/native_mean -B /tmp/native-build;
cmake --build /tmp/native-build; ctest --test-dir /tmp/native-build. CMake commands
are provided but NOT RUN here (cmake unavailable); g++ commands were executed.
Use MSVC/Clang builds separately before any cross-platform claim.
