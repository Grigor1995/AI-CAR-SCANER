# Cpp Feasibility Matrix

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

## A OBD protocol processing

- Current language / implementation: Python; ELM327Protocol, obd/decoding.py, vehicle/isotp/stack.py.
- Current measured performance: 0.0242 ms p50 snapshot; 0.0017 ms p50 DTC.
- Bottleneck / root cause: Short validated parsing; total adapter time unknown.
- Proposed C++ approach: Batch bytes through pybind11 only if high-rate CAN replay profiling warrants it.
- Non-C++ alternative: Precompile parsing patterns / avoid repeated normalization only after evidence.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Malformed frames, sequence and timeout handling are safety-sensitive.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **KEEP**. No production module qualifies MIGRATE TO C++ on this evidence.

## B Live telemetry

- Current language / implementation: Python; telemetry/analysis.py and service.py.
- Current measured performance: See paired.json: 1k/10k/50k entire summary.
- Bottleneck / root cause: Repeated sorted/filter passes plus exact averaging.
- Proposed C++ approach: C++20 mean C ABI prototype measured including ctypes conversion.
- Non-C++ alternative: Reuse prepared samples; fmean experiment is faster than native including copy.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Changing averaging rounding or quality/order changes conclusions.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **OPTIMIZE**. No production module qualifies MIGRATE TO C++ on this evidence.

## C Diagnostic engine

- Current language / implementation: Python; ai/reasoning and diagnostic/rules.py.
- Current measured performance: 0.5951 ms p50.
- Bottleneck / root cause: No current CPU budget pressure on deterministic fixture.
- Proposed C++ approach: Batch pure rule evaluator only if large real rule sets justify it.
- Non-C++ alternative: Normalize once / index rules after profiling representative evidence.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Hypotheses, test history, permissions and recommendations must remain identical.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **KEEP**. No production module qualifies MIGRATE TO C++ on this evidence.

## D AI processing

- Current language / implementation: Python HTTP orchestration; external native llama.cpp.
- Current measured performance: NOT MEASURED: no model loaded.
- Bottleneck / root cause: Model loading/token generation is not Python rule latency.
- Proposed C++ approach: Reuse existing llama.cpp runtime; no new inference engine.
- Non-C++ alternative: Tune context, quantization and streaming with actual model measurements.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Provider offline/error/cancellation contracts and grounding.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **DEFER**. No production module qualifies MIGRATE TO C++ on this evidence.

## E Serialization

- Current language / implementation: Python Pydantic and JSON snapshots.
- Current measured performance: 0.0047 ms p50.
- Bottleneck / root cause: Small fixture serialization is cheap; large historical sessions unknown.
- Proposed C++ approach: Native JSON encoder only after representative payload profiling.
- Non-C++ alternative: Avoid repeated dumps, batch persistence if transaction contract allows.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Unicode, field visibility, exact wire schema.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **KEEP**. No production module qualifies MIGRATE TO C++ on this evidence.

## F Backend processing

- Current language / implementation: Python FastAPI; SQLAlchemy.
- Current measured performance: 2.3438 ms p50 isolated TestClient health.
- Bottleneck / root cause: In-process health does not establish network or concurrent throughput.
- Proposed C++ approach: In-process extension for CPU work only; no separate microservice now.
- Non-C++ alternative: Profile database and session middleware under controlled socket concurrency.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Authentication, consent, legacy gating and transaction isolation.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **DEFER**. No production module qualifies MIGRATE TO C++ on this evidence.

## G Visualization

- Current language / implementation: Python QPainter; Kotlin Canvas; SwiftUI.
- Current measured performance: Desktop source offscreen evidence separate; device GPU NOT MEASURED.
- Bottleneck / root cause: Layout and frame scheduling differ from sample arithmetic.
- Proposed C++ approach: Bounded timeseries downsampling core only if measured frame pressure.
- Non-C++ alternative: Bound rendered points, coalesce refreshes, reuse decoded images with invalidation.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Do not drop diagnostic events or redesign existing UI.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **DEFER**. No production module qualifies MIGRATE TO C++ on this evidence.

## H Catalog/search

- Current language / implementation: Python JSON/SQL and lexical/vector RAG.
- Current measured performance: NOT MEASURED at production corpus size.
- Bottleneck / root cause: JSON rereads and linear scans are inspection findings, not proven bottlenecks.
- Proposed C++ approach: Native index only if Python/SQL indexes fail realistic targets.
- Non-C++ alternative: Indexes, cached immutable snapshots with version invalidation, top-k selection.
- Estimated speedup: NOT ESTIMATED without representative evidence; prototype numbers are measured in native.json, not extrapolated.
- Complexity: native introduces toolchains, packaging, ownership and error translation; selected Python change is low complexity.
- Integration overhead: Python/native copies and call cost measured for B; other bindings NOT MEASURED.
- Memory: Python traced peaks measured for B; native allocator/RSS NOT MEASURED. Avoid copies for any future binding.
- Cross-platform: shared backend Python path remains portable; native Linux prototype only. Windows/Android JNI/iOS wrappers NOT VERIFIED.
- Regression risk: Stale catalog, VIN uncertainty and fitment/protocol correctness.
- Maintenance cost: Python path retains existing dependencies; native implies per-ABI artifacts and compiler/runtime lifecycle.
- Final recommendation: **DEFER**. No production module qualifies MIGRATE TO C++ on this evidence.
