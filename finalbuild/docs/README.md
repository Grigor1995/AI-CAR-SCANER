# AI Auto Diagnostic Platform — Documentation

This documentation describes the implemented architecture of the finalbuild/ product.

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

The platform is **evidence-driven first, AI-assisted second**. Deterministic diagnostic logic is responsible for facts, hypothesis categories, test planning, and evidence state. Retrieval and LLM components provide contextual knowledge and explanations; they are not the source of truth for vehicle measurements.

## Implemented product shape

- FastAPI modular-monolith backend and Pydantic session models.
- SQLAlchemy persistence foundations and PostgreSQL/pgvector Docker deployment.
- Deterministic diagnostic rules and information-gain/cost/safety-based test selection.
- Optional local LLM through standalone llama-server.exe.
- RAG foundation with metadata filtering and reranking seams.
- OBD/VCI abstraction, simulator, telemetry/acquisition services, and vehicle/network discovery foundations.
- Native PySide6 Desktop, Kotlin/Jetpack Compose Android, and SwiftUI iOS clients.
- Unit/API/integration/regression tests and CI workflows.

## Important implementation note

The repository contains both a normalized SQLAlchemy schema and complete-session snapshot persistence (diagnostic_session_state). The API keeps DiagnosticSession objects in an in-process registry for fast reasoning and persists snapshots when DATABASE_URL is configured. This documentation describes the current implementation rather than presenting future architecture as complete.
