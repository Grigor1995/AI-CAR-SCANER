# Dependency Map

## 1. External runtime dependencies

| Dependency | Role | Boundary |
|---|---|---|
| FastAPI | HTTP API | backend/api |
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
| NumPy | Transitive dependency of optional embedding providers; not required by core runtime | requirements-ai.txt |
| pytest | Test framework | tests |
| pytest-asyncio | Async tests | tests |
| httpx | API/client tests | tests |
| ruff | Static linting | CI/dev |
| sentence-transformers | Optional embedding dependency | requirements-ai.txt |
| fastembed | Optional embedding dependency | requirements-ai.txt |
| llama-server.exe | Local LLM runtime | external process |
| GGUF model | Local model weights | models/ |

## 2. Internal dependency direction

Preferred direction:

~~~text
Native clients
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

AI enriches diagnostic evidence and must not become a hidden dependency of deterministic analysis:

~~~text
DiagnosticSession
    ↓
Deterministic reasoning
    ↓
AI reasoning / RAG / LLM
    ↓
Explanation + context + suggested orchestration
~~~

## 3. Main internal edges

| From | To | Why |
|---|---|---|
| api.main | diagnostic.models | API contracts |
| api.main | diagnostic.rules | deterministic analysis |
| api.main | diagnostic.decision | test planning |
| api.main | ai.reasoning.engine | intelligence enrichment |
| api.state | diagnostic.session_persistence | session durability |
| ai.reasoning.engine | diagnostic.rules | deterministic core |
| ai.reasoning.engine | diagnostic.decision | test selection |
| ai.reasoning.engine | ai.ml | numeric anomaly analysis |
| ai.reasoning.pipeline | ai.rag | knowledge retrieval |
| ai.reasoning.pipeline | ai.llm.interfaces_guard | safe prompt context |
| ai.llm.factory | ai.llm.llama_server | local provider |
| ai.llm.factory | ai.llm.openai_compatible | alternate provider |
| device.manager | simulator | current deterministic VCI implementation |
| acquisition.service | telemetry | normalized samples |
| api | network_discovery | discovery endpoints |
| api | multi_ecu / multi_bus | vehicle network APIs |

## 4. Dependency rules

- **Transport independence:** diagnostic logic must not depend directly on BLE/Wi-Fi/USB implementation details.
- **LLM optionality:** deterministic analysis must remain useful when the LLM is unavailable.
- **Evidence provenance:** AI output must remain distinguishable from direct measurement and technician observation.
- **Thin clients:** clients should call backend capabilities instead of implementing separate diagnostic rules.
- **Replaceable infrastructure:** persistence, local LLM runtime, VCI adapters, and embedding providers should use stable interfaces where practical.

## 5. Current architectural risks

### R1 — Two persistence representations
Normalized SQLAlchemy tables and complete JSON session snapshots coexist. Define the authoritative representation for long-lived relational queries.

### R2 — Runtime registry
api/state.py stores active sessions in a process-local dictionary. Multiple API workers do not automatically share this in-memory registry.

### R3 — Application/domain coupling
Some API routes instantiate domain engines directly. An application-service layer would clarify orchestration and persistence boundaries.

### R4 — Retrieval implementation
HybridKnowledgeStore is an extensible foundation, but its current search implementation is lexical. Do not describe embeddings/pgvector as the active retrieval path unless the runtime actually uses it.

### R5 — Client implementation boundaries
The active clients are PySide6 Desktop, native Android, and native iOS. Keep platform status and feature limitations explicit so documentation does not imply unsupported parity.

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
