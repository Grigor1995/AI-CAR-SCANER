# System Architecture Overview

## 1. What the system is designed for

AI Auto Diagnostic Platform is a cross-platform automotive diagnostic system designed to answer:

> **What is the most useful and safest next diagnostic action, given the evidence currently available?**

It is not only an OBD scanner and it is not an LLM chatbot.

The product is designed to start a diagnostic session from several entry points:

1. Manual symptom description.
2. Manually entered DTC.
3. OBD/VCI data.
4. Live telemetry.
5. Existing persisted diagnostic session.
6. Vehicle/network discovery.
7. Future custom Android diagnostic hardware.

The central business object is `DiagnosticSession`.

## 2. Architectural style

The current implementation is a **modular monolith**.

There is one primary FastAPI application process, but the backend is divided into explicit domain modules:

- `api` — HTTP boundary.
- `diagnostic` — diagnostic domain and reasoning.
- `ai` — evidence extraction, reasoning, ML, RAG and LLM adapters.
- `device` — VCI/device lifecycle.
- `acquisition` — telemetry acquisition.
- `multi_ecu`, `multi_bus`, `network_discovery` — vehicle network capabilities.
- `platform`, `professional_platform`, `security`, `observability` — cross-cutting/platform capabilities.
- `telemetry`, `vehicle`, `models`, `datasets`, `tests` — supporting domains and verification.

This gives the project service boundaries without prematurely splitting the product into microservices.

## 3. High-level architecture

~~~mermaid
flowchart TB
    subgraph Clients["Client layer"]
      D["Desktop workstation"]
      A["Android / mobile"]
      W["Web foundation"]
      F["Future custom Android diagnostic device"]
    end

    subgraph Backend["FastAPI modular monolith"]
      API["API / REST routers"]
      DOMAIN["Diagnostic domain"]
      INTEL["Diagnostic Intelligence"]
      RAG["RAG / Knowledge"]
      LLM["LLM provider boundary"]
      DEVICE["Device / VCI abstraction"]
      ACQ["Telemetry acquisition"]
      DISC["ECU / CAN / network discovery"]
      PLATFORM["Platform / security / observability"]
    end

    subgraph Data["Data & runtime"]
      DB["PostgreSQL + pgvector"]
      SNAP["Diagnostic session snapshots"]
      KB["Knowledge / datasets"]
      SIM["Vehicle / VCI simulators"]
      LOCAL["llama-server.exe + GGUF model"]
    end

    D --> API
    A --> API
    W --> API
    F --> DEVICE
    API --> DOMAIN
    API --> INTEL
    API --> DEVICE
    API --> ACQ
    API --> DISC
    INTEL --> DOMAIN
    INTEL --> RAG
    INTEL --> LLM
    DEVICE --> SIM
    ACQ --> SIM
    RAG --> KB
    LLM --> LOCAL
    DOMAIN --> SNAP
    DOMAIN --> DB
    RAG --> DB
    PLATFORM -. cross-cutting .-> API
    PLATFORM -. cross-cutting .-> DOMAIN
~~~

## 4. Runtime responsibilities

### Client layer

Clients are presentation and interaction surfaces. They should not duplicate the diagnostic rules.

The desktop application additionally acts as a Windows workstation/runtime launcher: it can manage the local llama-server and FastAPI lifecycle and expose the diagnostic UI.

### API layer

`backend/api/main.py` creates the FastAPI application and registers route groups for:

- sessions
- intelligence
- AI
- knowledge
- RAG
- decisions
- telemetry
- acquisition
- vehicle diagnostics
- multi-ECU
- multi-bus
- network discovery
- active discovery
- devices
- vehicle catalog
- platform/security related capabilities

### Diagnostic domain

The domain owns:

- `DiagnosticSession`
- vehicle identity
- symptoms
- DTCs
- evidence
- hypotheses
- diagnostic tests
- test results
- measurements
- live data
- audit events
- diagnostic state transitions

`DiagnosticReasoningEngine` applies deterministic rules and deliberately avoids declaring unsupported component failures as confirmed.

### Intelligence layer

`DiagnosticIntelligenceEngine` adds:

1. Structured evidence extraction.
2. Evidence normalization.
3. Deterministic reasoning.
4. Numeric anomaly analysis.
5. Missing-question identification.
6. Decision/test planning.
7. Evidence-linked scoring.

The important design rule is:

**AI enriches the diagnostic loop; deterministic evidence remains authoritative.**

### RAG layer

`DiagnosticIntelligencePipeline` combines deterministic analysis with:

- knowledge retrieval,
- lexical reranking,
- safe prompt-context construction,
- optional LLM generation.

The current `HybridKnowledgeStore` is a local RAG foundation. Its current search implementation is lexical; embedding providers and pgvector infrastructure exist as extension points.

### LLM layer

The provider factory selects a provider through `DIAGNOSTIC_LLM_PROVIDER`.

The current default is `llama-server`.

The local runtime is deliberately external to Python:

- standalone `llama-server.exe`
- local GGUF model
- HTTP API boundary

This keeps the backend independent from a Python `llama_cpp` binding.

## 5. Why this architecture exists

### Offline-first

A vehicle can be diagnosed from manually supplied evidence without an internet connection or physical adapter.

### Deterministic safety

A model should not invent measured values or silently convert a possibility into a confirmed mechanical failure.

### Hardware independence

The diagnostic domain should not know whether data came from BLE, Wi-Fi, USB, a simulator, J2534, or a future custom device.

### Cross-platform clients

Desktop and mobile clients use the same backend/domain contract rather than maintaining independent diagnostic implementations.

### Incremental evolution

The modular-monolith approach allows the system to grow from software-only diagnostics into OBD, CAN/UDS, professional VCI and custom hardware without forcing an early microservice migration.
