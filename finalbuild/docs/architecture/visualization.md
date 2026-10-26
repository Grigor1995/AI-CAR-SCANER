# Architecture Visualizations

## Interactive architecture explorer (animated HTML)

Open [AI CAR SCANNER interactive architecture map](AI_CAR_SCANNER_architecture_map.html) locally in a browser to explore the animated, clickable system. Select a use-case and click nodes/arrows to inspect the high-level call paths. [Short overview](AI_CAR_SCANNER_architecture_summary.md).

The visualization is an architectural model, **not** an automatically generated function-level runtime trace; confirm exact endpoint/function hops against the current implementation before relying on it for debugging.

All diagrams in this document are Mermaid source so they remain editable and version-controlled with the architecture.

## 1. System context

~~~mermaid
flowchart TB
    USER["Technician / vehicle owner"]
    DESKTOP["Desktop workstation"]
    MOBILE["Android / mobile"]
    VEHICLE["Vehicle / ECU network"]
    DEVICE["OBD / VCI / future diagnostic device"]
    PLATFORM["AI Auto Diagnostic Platform"]
    KNOWLEDGE["OEM docs / curated cases / datasets"]
    LLM["Local llama-server + GGUF"]
    DB["PostgreSQL / pgvector"]

    USER --> DESKTOP
    USER --> MOBILE
    DESKTOP --> PLATFORM
    MOBILE --> PLATFORM
    VEHICLE <--> DEVICE
    DEVICE <--> PLATFORM
    KNOWLEDGE --> PLATFORM
    PLATFORM <--> LLM
    PLATFORM <--> DB
~~~

## 2. Container view

~~~mermaid
flowchart LR
    subgraph UI["Presentation"]
      Desktop
      Android
      Mobile
    end

    subgraph APP["Application"]
      API["FastAPI routers"]
      Session["Session runtime"]
      Diagnostic["Diagnostic engines"]
      Intelligence["AI intelligence"]
      Device["Device manager"]
      Acquisition["Acquisition"]
      Discovery["Network discovery"]
    end

    subgraph INFRA["Infrastructure"]
      PostgreSQL
      PGVector["pgvector"]
      Llama["llama-server"]
      Simulator["Vehicle/VCI simulator"]
    end

    UI --> API
    API --> Session
    API --> Diagnostic
    API --> Intelligence
    API --> Device
    API --> Acquisition
    API --> Discovery

    Session --> PostgreSQL
    Intelligence --> Diagnostic
    Intelligence --> PGVector
    Intelligence --> Llama
    Device --> Simulator
    Acquisition --> Simulator
~~~

## 3. Diagnostic sequence

~~~mermaid
sequenceDiagram
    participant U as User/Technician
    participant API as FastAPI
    participant S as DiagnosticSession
    participant R as Rules Engine
    participant I as Intelligence Engine
    participant D as Decision Engine
    participant T as Vehicle/Test
    participant K as RAG
    participant L as LLM

    U->>API: create/update session
    API->>S: store vehicle/symptom/DTC
    API->>S: create evidence
    U->>API: analyze
    API->>I: analyze(session)
    I->>R: deterministic analysis
    R-->>I: hypotheses + rule recommendations
    I->>D: refresh recommendations
    D-->>I: ranked tests
    I->>K: retrieve relevant knowledge
    K-->>I: ranked context
    I->>L: optional safe prompt
    L-->>I: explanation/orchestration
    I-->>API: enriched session
    API-->>U: hypotheses + next tests

    U->>API: record test result
    API->>S: append measured evidence
    API->>I: re-analyze
    I->>R: recompute hypotheses
    I->>D: recompute next test
    I-->>API: updated plan
~~~

## 4. Evidence provenance

~~~mermaid
flowchart LR
    USER["User statement"] --> E1["USER_REPORTED"]
    TECH["Technician observation"] --> E2["TECHNICIAN_OBSERVED"]
    ECU["ECU / DTC"] --> E3["ECU_REPORTED"]
    SENSOR["Live measurement"] --> E4["VEHICLE_MEASURED"]
    RULE["Rule engine"] --> E5["RULE"]
    ML["ML detector"] --> E6["ML_MODEL"]
    LLM["LLM"] --> E7["LLM_INFERENCE"]

    E1 --> STATUS["Evidence status"]
    E2 --> STATUS
    E3 --> STATUS
    E4 --> STATUS
    E5 --> STATUS
    E6 --> STATUS
    E7 --> STATUS

    STATUS --> H["Hypotheses"]
    H --> TEST["Diagnostic test"]
    TEST --> E2
    TEST --> E4
~~~

## 5. Decision loop

~~~mermaid
flowchart TD
    H["Current hypotheses"] --> C["Candidate tests"]
    C --> IG["Expected information gain"]
    C --> FIT["Evidence fit"]
    C --> COST["Estimated cost"]
    C --> RISK["Safety/risk"]
    IG --> SCORE["Priority score"]
    FIT --> SCORE
    COST --> SCORE
    RISK --> SCORE
    SCORE --> NEXT["Next diagnostic action"]
    NEXT --> OBS["Observed result"]
    OBS --> E["New evidence"]
    E --> H
~~~

## 6. Deployment view

~~~mermaid
flowchart TB
    subgraph Windows["Windows workstation"]
      App["AI Car Scanner desktop launcher"]
      API["FastAPI :8001"]
      Llama["llama-server :8000"]
      Model["Qwen3 GGUF / configured local model"]
    end

    subgraph Docker["Docker environment"]
      PG["PostgreSQL / pgvector :5432"]
      Backend["Containerized backend"]
    end

    subgraph DeviceLayer["Vehicle side"]
      VCI["OBD/VCI adapter"]
      Car["Vehicle ECUs / CAN"]
    end

    App --> Llama
    App --> API
    API --> Llama
    API --> PG
    Backend --> PG
    VCI <--> Car
    API <--> VCI
~~~

The exact ports/runtime mode can differ between local and Docker workflows; the diagrams describe the documented Windows local runtime and the Docker deployment separately.

## 7. Architectural hierarchy

~~~mermaid
mindmap
  root((AI Auto Diagnostic))
    Clients
      Desktop
      Android
      Mobile
      Future device
    Backend
      API
      Diagnostic
        Session
        Evidence
        Rules
        Decision
      AI
        Reasoning
        RAG
        LLM
        ML
        Evaluation
      Device
      Acquisition
      Telemetry
      Discovery
    Data
      PostgreSQL
      pgvector
      Snapshots
      Datasets
    Quality
      Unit
      API
      Integration
      Regression
      Simulator
      Golden cases
      AI grounding
~~~
