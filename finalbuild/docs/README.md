# AI Auto Diagnostic Platform — Documentation

This documentation describes the implemented architecture of the `finalbuild/` product as it exists in the repository.

## Documentation map

| Document | Purpose |
|---|---|
| [Architecture overview](architecture/system-overview.md) | Product purpose, architectural style, runtime topology, major boundaries |
| [Domain & diagnostic flow](architecture/domain-and-flow.md) | DiagnosticSession, evidence, hypotheses, tests, state flow, end-to-end execution |
| [Component hierarchy](architecture/component-hierarchy.md) | Repository hierarchy and responsibility of each major package |
| [Dependency map](architecture/dependency-map.md) | External dependencies and internal dependency direction |
| [Visualizations](architecture/visualization.md) | Mermaid diagrams for system, data, sequence, deployment and dependency views |
| [Phase architecture](architecture/) | Historical phase-by-phase architecture decisions |
| [Device architecture](device/) | Device/VCI evolution and transport documentation |

## Architecture principle

The platform is **evidence-driven first, AI-assisted second**.

The deterministic diagnostic domain is responsible for facts, hypothesis categories, test planning and evidence state. Retrieval and LLM components provide contextual knowledge, explanations and orchestration; they are not the source of truth for vehicle measurements.

## Implemented product shape

- FastAPI modular-monolith backend.
- Pydantic domain/session models.
- SQLAlchemy persistence foundations.
- PostgreSQL/pgvector Docker deployment.
- Deterministic diagnostic rules.
- Information-gain/cost/safety based test selection.
- Local LLM boundary through standalone `llama-server.exe`.
- RAG foundation with metadata filtering and reranking seams.
- OBD/VCI abstraction and simulator.
- Telemetry/acquisition services.
- Vehicle/network discovery foundations.
- Desktop workstation plus Android/mobile foundations.
- Automated unit/API/integration/regression coverage and CI.

## Important implementation note

The repository contains both a normalized SQLAlchemy schema (`vehicles`, `diagnostic_sessions`, `evidence`, `vehicle_catalog_entries`) and the current complete-session snapshot persistence mechanism (`diagnostic_session_state`). The API keeps `DiagnosticSession` objects in an in-process registry for fast reasoning and persists snapshots when `DATABASE_URL` is configured.

This documentation intentionally describes that **current implementation**, rather than presenting a future repository pattern as if it were already complete.
