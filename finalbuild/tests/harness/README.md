# Diagnostic Test Harness

The harness is client-independent. Desktop and Android do not carry their own diagnostic datasets.

## Canonical global data

- `data/global/vehicles.json`
- `data/global/diagnostic_cases.json`
- `backend/global_data.py`
- `GET /api/v1/global-data`

The same data is consumed by the backend, API clients and golden tests.

## Golden cases

| Case | Purpose |
|---|---|
| LPG_MISFIRE_001 | LPG-only low-RPM misfire; blocks unsupported coil/injector/mechanical confirmation |
| LEAN_MIXTURE_001 | Petrol lean-mixture baseline |

## Test layers

1. Global-data contract tests.
2. Golden diagnostic cases.
3. API contract tests.
4. Existing unit/integration/regression suites.
5. Deterministic performance test.
6. Whole-backend line coverage.

## Commands

Run the focused harness:

pytest -q tests/harness

Run coverage:

pytest -q --cov=backend --cov-report=term-missing --cov-report=xml --cov-fail-under=60

Run the deterministic performance benchmark:

pytest -q tests/harness/test_performance.py -vv

## Performance targets

- deterministic reasoning p95 < 90 ms
- ordinary API p95 < 500 ms
- DTC processing < 200 ms
- RAG retrieval < 500 ms

The performance test reports measured p50/p95 values. It never pretends that a target is a measured result.

## Architecture rule

All diagnostic data and session state are backend/global concerns. Mobile and desktop are presentation clients only.
