# Current Architecture Analysis

## Executive assessment

The repository has evolved beyond a simple prototype. It already contains the major boundaries needed for a production-oriented diagnostic platform:

- evidence-driven domain model;
- deterministic reasoning;
- information-gain-oriented diagnostic decisions;
- local LLM boundary;
- RAG and grounding foundations;
- VCI/device abstraction;
- telemetry acquisition;
- vehicle/network discovery;
- cross-platform client foundations;
- simulator and golden-case testing;
- CI and Docker infrastructure.

The strongest architectural choice is the separation between **deterministic diagnostic truth** and **AI assistance**.

## Architecture maturity

| Area | Current maturity | Observation |
|---|---|---|
| Domain model | Strong | DiagnosticSession and evidence provenance are explicit |
| Deterministic reasoning | Strong | Rules engine is scenario-aware and evidence-linked |
| Decision support | Strong foundation | Information gain, cost and safety are modeled |
| AI orchestration | Good foundation | Reasoning pipeline and safe prompt context exist |
| Local LLM | Good | External llama-server boundary is clean |
| RAG | Foundation | Current store is lexical; richer vector path is an extension |
| Persistence | Transitional | Normalized schema and snapshot persistence coexist |
| Device abstraction | Foundation/strong | Simulator and capability model exist |
| Physical adapters | Partial | Simulator is authoritative in the current device manager path |
| Multi-ECU/network | Foundation | Discovery modules exist and are exposed through API |
| Client architecture | Transitional | Multiple desktop/mobile implementations coexist |
| Testing | Strong foundation | Unit/API/integration/regression/golden-case structure exists |
| Observability/security | Foundation | Dedicated modules exist, but depth varies by subsystem |

## Key architectural strengths

### 1. DiagnosticSession is the correct aggregate

The session unifies vehicle identity, symptoms, DTCs, evidence, hypotheses and actions. This makes the diagnostic process explainable and replayable.

### 2. Evidence provenance is explicit

The source/status split prevents a user statement, ECU observation, calculated value and LLM inference from being treated as equivalent facts.

### 3. Deterministic reasoning is not hidden behind AI

The rules engine can operate without the LLM. This is essential for offline operation, reproducibility and regression testing.

### 4. The next-test concept is first-class

The product is not only trying to answer “what is broken?” It can answer “what should I test next?” This is a stronger architecture for real diagnostics because it creates a measurable diagnostic loop.

### 5. Hardware is abstracted

The diagnostic domain is not designed around one adapter vendor. The device manager and transport seams support the planned evolution toward real VCI/J2534/custom hardware.

## Current architectural gaps

### 1. Persistence boundary

The current API owns an in-memory session registry while persistence is handled by a snapshot helper.

Recommended target:

~~~text
API
 ↓
DiagnosticSessionApplicationService
 ↓
DiagnosticSessionRepository
 ↓
PostgreSQL
~~~

The current code can evolve to this without changing the domain model.

### 2. Worker/process scaling

Because active sessions are held in a process-local dictionary, multiple backend workers require a shared runtime state strategy.

Target options include:

- repository-backed session loading;
- Redis/cache for active state;
- optimistic versioning;
- explicit session locking where needed.

### 3. RAG implementation depth

The repository has the interfaces and infrastructure direction for embeddings/pgvector, but the current `HybridKnowledgeStore` search implementation is lexical.

The documentation therefore treats vector retrieval as a capability/foundation, not as the only active retrieval algorithm.

### 4. Client consolidation

There are current and legacy UI implementations. The canonical client should be identified and the legacy implementation eventually isolated or retired.

### 5. Application-service layer

Routes currently instantiate and invoke domain/intelligence engines directly. A dedicated application layer would make:

- transaction boundaries;
- authorization;
- persistence;
- event/audit handling;
- orchestration;
- background work

more explicit.

## Target architecture

The clean long-term structure is:

~~~text
Presentation
    ↓
API / Application services
    ↓
Domain
    ├── DiagnosticSession
    ├── Evidence
    ├── Hypotheses
    ├── DiagnosticDecision
    └── Rules
    ↓
Ports
    ├── SessionRepository
    ├── KnowledgeRepository
    ├── LLMProvider
    ├── EmbeddingProvider
    └── DiagnosticAdapter
    ↓
Adapters
    ├── PostgreSQL
    ├── pgvector
    ├── llama-server
    ├── BLE
    ├── Wi-Fi
    ├── USB
    ├── J2534
    └── Simulator
~~~

## Design objective

The final system should preserve this invariant:

> **No AI component is allowed to manufacture vehicle evidence. AI may interpret, retrieve, rank, explain or suggest; measurements and confirmed conclusions must remain traceable to evidence and diagnostic tests.**

That invariant is the architectural identity of the product.


## Implemented remediation

The previously identified issues have now been addressed in the implementation:

- **Shared session state:** the API session registry is now backed by shared persistence. With DATABASE_URL, PostgreSQL is the source of truth rather than a desktop/mobile-local store.
- **Single-session persistence:** persistence exposes save_one() so new sessions are immediately durable and visible to other API processes/clients.
- **Client-independent global data:** canonical vehicle/test data lives under data/global/ and is exposed through /api/v1/global-data. Desktop and Android are consumers, not owners.
- **Test harness:** global-data contract tests, golden diagnostic cases and deterministic performance tests were added.
- **Coverage:** CI now runs pytest-cov and enforces a whole-backend minimum line coverage gate of 60%.
- **Performance:** the deterministic reasoning harness measures p50/p95 and enforces a p95 budget of 100 ms.

## Remaining deliberate limitations

- Concurrent writes to the same diagnostic session are still last-write-wins. A future optimistic version column/ETag can provide conflict detection.
- Physical VCI transports remain phase-dependent; the simulator remains the deterministic integration adapter.
- RAG currently has a lexical active path; vector/embedding infrastructure remains an extension point.
