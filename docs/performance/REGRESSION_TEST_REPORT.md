# Regression test report

2026-10-29, Linux cloud host, existing AI-CAR-SCANER repository.

| Check | Actual result |
|---|---|
| Before merge push | PASS: 1001 passed, 2 skipped, 41.96 s |
| Full common suite after production optimization | PASS: 1062 passed, 2 skipped, 44.47 s |
| Targeted equivalence/telemetry/performance-tool after tool correction | PASS: 71 passed, 1.56 s |
| Desktop five isolated groups | PASS: logic 216 + 1 skip; e2e 6; negative 68; UI-POM 142; widgets 25 |
| Desktop source coverage | MEASURED: 90.43%, production core 90.84%; no gate requested in this run |
| Real temporary SQLite migration + HTTP + restart | PASS: 10 checks; auth, invite, scope, revoke and persistence |
| Paired frozen-reference equivalence | PASS: 1k/10k/50k; stats exact, fresh UUID/time excluded |
| Added randomized/boundary equivalence | PASS: 61 cases; invalid-only, empty, mixed quality, duplicate time/sequence, append, no mutation |
| Native contract executable | PASS: g++ C++20 ASan/UBSan; null/empty/nonfinite/cancellation/extreme finite cases |
| Native numerical pipeline fixture | PASS at tolerance 1e-12; NOT proof of universal exact rounding |
| Chromium dashboard | PASS: 12 checks, actual CDP input for pan/wheel; 420px responsive |
| Static checks | PASS: JS syntax, Ruff F401/F811/F821/F841 on new Python, git diff --check |
| Android build / source instrumentation compile / JVM / APK / lint | PASS: 14 s, 67 tasks, 1 executed/66 up-to-date; cached JVM task results |
| Android emulator/device / physical OBD | NOT RUN / BLOCKED: no hardware |
| iOS Xcode | BLOCKED: Linux environment |
| Windows EXE/installer | NOT RUN: no Windows environment |
| Live PostgreSQL/concurrent socket load/real LLM | NOT RUN |

Tests do not establish production readiness or all-vehicle protocol coverage.
Baseline and current JSON, rejected candidate, CPU/allocation observations and
browser checks are retained under evidence/. Android cached results are not
reported as newly executed JVM tests. Native thread sanitizer and platform ABI
packaging are NOT RUN; native code is experimental, not application runtime.

A failed initial browser responsiveness check exposed overflow in this NEW report
page, fixed with wrapping/bounded content and rechecked PASS; application UI
unchanged. Initial Desktop timing helper failed on missing inert base_url metadata;
helper fixed and actual benchmark rerun. Both are tooling findings, not hidden
application performance regressions.
