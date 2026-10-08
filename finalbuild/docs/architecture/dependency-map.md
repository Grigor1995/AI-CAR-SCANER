# Dependency Map

## 1. External runtime dependencies

| Dependency | Role | Boundary |
|---|---|---|
| FastAPI | HTTP API | `backend/api` |
| Uvicorn | ASGI server | runtime |
| Pydantic | Domain/request validation | backend-wide |
| SQLAlchemy | Persistence/ORM | persistence |
| psycopg | PostgreSQL driver | persistence |
| Alembic | DB migration tooling | infrastructure/persistence |
| PostgreSQL | Shared durable data | Docker/runtime |
| pgvector image | Vector-capable PostgreSQL runtime | Docker |
| Bleak | Bluetooth transport | device/OBD |
| pyserial | USB/serial transport | device/OBD |
| PyYAML | Dataset/config parsing | ingestion/runtime |
| pypdf | PDF knowledge ingestion | AI ingestion |
| NumPy | Numeric/AI evaluation runtime | ML/evaluation |
| pytest | Test framework | tests |
| pytest-asyncio | Async tests | tests |
| httpx | API/client tests | tests |
| ruff | Static linting | CI/dev |
| sentence-transformers | Optional embedding dependency | `requirements-ai.txt` |
| fastembed | Optional embedding dependency | `requirements-ai.txt` |
| llama-server.exe | Local LLM runtime | external process |
| GGUF model | Local model weights | `models/` |

## 2. Internal dependency direction

Preferred direction:

~~~text
Clients
  ↓
API
  ↓
Application/domain orchestration
  ↓
Diagnostic domain
  ↓
Ports/interfaces
  ↓
Infrastructure adapters
~~~

AI is intentionally a consumer/enricher of diagnostic evidence:

~~~text
DiagnosticSession
    ↓
Deterministic reasoning
    ↓
AI reasoning / RAG / LLM
    ↓
Explanation + context + suggested orchestration
~~~

The LLM must not become a hidden dependency of the deterministic diagnostic engine.

## 3. Main internal edges

| From | To | Why |
|---|---|---|
| `api.main` | `diagnostic.models` | API contracts |
| `api.main` | `diagnostic.rules` | deterministic analysis |
| `api.main` | `diagnostic.decision` | test planning |
| `api.main` | `ai.reasoning.engine` | intelligence enrichment |
| `api.state` | `diagnostic.session_persistence` | session durability |
| `ai.reasoning.engine` | `diagnostic.rules` | deterministic core |
| `ai.reasoning.engine` | `diagnostic.decision` | test selection |
| `ai.reasoning.engine` | `ai.ml` | numeric anomaly analysis |
| `ai.reasoning.pipeline` | `ai.rag` | knowledge retrieval |
| `ai.reasoning.pipeline` | `ai.llm.interfaces_guard` | safe prompt context |
| `ai.llm.factory` | `ai.llm.llama_server` | local provider |
| `ai.llm.factory` | `ai.llm.openai_compatible` | alternate provider |
| `device.manager` | simulator | current deterministic VCI implementation |
| `acquisition.service` | `telemetry` | normalized samples |
| `api` | `network_discovery` | discovery endpoints |
| `api` | `multi_ecu` / `multi_bus` | vehicle network APIs |

## 4. Dependency rules

### Rule A — Transport independence

`diagnostic` must not depend directly on BLE/Wi-Fi/USB implementation details.

### Rule B — LLM optionality

The system must remain useful when the LLM is unavailable.

The repository explicitly supports deterministic analysis without live LLM inference.

### Rule C — Evidence provenance

AI output must be distinguishable from direct measurement and technician observation.

### Rule D — Client thinness

Clients should call backend capabilities instead of implementing separate diagnostic rules.

### Rule E — Infrastructure replaceability

PostgreSQL, local LLM runtime, VCI adapters and embedding providers should be accessed through stable seams where practical.

## 5. Current architectural risks

### R1 — Two persistence representations

The repository contains normalized SQLAlchemy tables and a complete JSON snapshot table. They currently coexist.

**Implication:** future work should define which model is authoritative for long-lived relational querying and whether the snapshot remains the session aggregate cache.

### R2 — Runtime registry

`api/state.py` stores active sessions in a process-local dictionary.

**Implication:** multiple API workers would not automatically share the in-memory registry.

### R3 — Application/domain coupling

Some API routes instantiate domain engines directly.

**Implication:** a future `DiagnosticSessionService` / application-service layer would make orchestration and persistence boundaries cleaner.

### R4 — RAG naming vs implementation

`HybridKnowledgeStore` is an extensible foundation, but its current search implementation is lexical. Embedding/pgvector capabilities should not be documented as the only active retrieval path unless the runtime path actually uses them.

### R5 — Multiple client implementations

Desktop, legacy Flutter desktop, Flutter/mobile and native Android coexist.

**Implication:** client lifecycle/status should be documented explicitly so legacy implementations are not mistaken for the canonical UI.

## 6. Dependency graph

~~~mermaid
flowchart LR
    API["FastAPI API"] --> DOM["Diagnostic Domain"]
    API --> AI["AI / RAG"]
    API --> DEV["Device"]
    API --> ACQ["Acquisition"]

    AI --> DOM
    AI --> RAG["RAG"]
    AI --> LLM["LLM adapters"]
    AI --> ML["ML"]

    DOM --> DB["SQLAlchemy / PostgreSQL"]
    DEV --> BT["BLE / Serial / future VCI"]
    ACQ --> TEL["Telemetry"]

    RAG --> EMB["Embedding providers"]
    RAG --> DB
    LLM --> LS["llama-server.exe"]
    ML --> NUM["NumPy"]
~~~
