# Cpp Integration Architecture

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

Production: no new native extension, JNI, Objective-C++, worker or service.
Experiments/native_mean exposes only telemetry_mean(const double*, size_t,
double*) noexcept. Caller owns immutable input/output buffers for duration of
call; return 0 success, 1 bad pointer/empty input, 2 nonfinite input, 3 overflow.
No exception crosses C ABI; no global mutable state, allocations or I/O.
The ctypes wrapper owns packed arrays with Python scope lifetime; GIL is released
by CDLL during native call, not during conversion. Shared-library symbols use
Windows dllexport / ELF visibility; only Linux compiled/tested.

Prototype is not a drop-in replacement: finite-only validation and long-double
rounding differ from Python's exact rational statistics.mean, and long double
precision varies by platform. Output fixtures pass tolerance, not universal
bitwise equivalence. C++ prototype must never become an automatic fallback.

If future profiling justifies integration: use a pure-domain batch processor
behind a narrow protocol, optional pybind11 with explicit borrowed contiguous
buffer ownership, typed exceptions and GIL release only around immutable native
work. Preserve Python fallback and compare outputs per deployment. Backend shared
logic means no mobile JNI/Swift wrapper is needed unless computation must execute
on-device; JNI needs ABI/NDK matrix and Objective-C++ needs Apple toolchain proof.
Do not create an RPC service for a microsecond operation.
