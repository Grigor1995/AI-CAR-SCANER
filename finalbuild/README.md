# AI Auto Diagnostic Platform

Evidence-driven, offline-capable automotive diagnostic platform. Phase 1 is a software-only MVP with manual diagnostics, deterministic rules, local AI interfaces, RAG interfaces, a vehicle simulator, and automated regression testing.

## Phase 1 status
- Repository scaffold
- FastAPI backend skeleton
- PostgreSQL schema + SQLAlchemy models
- DiagnosticSession domain model
- Evidence/provenance model
- Hardware/LLM/embedding interfaces
- Deterministic rules engine
- Vehicle simulator + failure scenarios
- Golden diagnostic case: `LPG_MISFIRE_001`
- Unit/API/integration/regression tests
- Docker Compose for PostgreSQL + API
- CI pipeline
- Native PySide6 desktop workstation plus Android/mobile source foundations

## Run backend locally
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --host 127.0.0.1 --port 8001
```

API: http://127.0.0.1:8001/docs

## Build all native applications

Use the repository-root runner: `python ../build.py --check` from this folder.
For a complete Desktop/Android/iOS build, run **Build all native apps** in GitHub
Actions or `python ../build.py --ci --with-tests` with authenticated GitHub CLI.
[Local builds, toolchain setup and artifacts](docs/building/BUILD_ALL.md).

## Run tests

[Branch integration review — 22 October 2026](docs/testing/branch-merge-review-2026-10-22.md) records all remote branch tips, conflict decisions and the validated combined result.

[Native UI demo and QA presentation — 22 October 2026](docs/demo/README.md) includes the editable PowerPoint deck, real UI captures and the Session ID privacy follow-up.

See the [October 21 full QA audit](docs/testing/full-qa-audit-2026-10-21.md) for measured coverage, fixes, remaining gaps and reproduction commands.
```bash
pip install -r backend/requirements-dev.txt
pytest -q
```

## Docker
```bash
docker compose up --build
```

## Architecture
See [system overview](docs/architecture/system-overview.md) and [domain flow](docs/architecture/domain-and-flow.md).

## Phase 2 — Generic OBD

Phase 2 adds vendor-neutral OBD-II support through transport adapters:
- BLE/GATT
- Wi-Fi/TCP
- USB/serial
- simulator transport

Supported generic operations:
- VIN
- DTCs
- RPM
- coolant temperature
- vehicle speed
- throttle position

Run tests from repository root:
```bash
python -m pytest tests -q
```

See [system overview](docs/architecture/system-overview.md) for implementation boundaries and [component hierarchy](docs/architecture/component-hierarchy.md) for adapters.

## Phase 4
Professional VCI abstraction is included: device registry/capabilities, adapter lifecycle, generic vendor SDK seam, J2534 Pass-Thru interface, Windows DLL loading seam, VCI simulator and tests.

## Phase 7
Production security and observability foundations are included in `backend/security`, `backend/observability`, and `backend/platform/tenant.py`.

## Phase 9
Real RAG/local LLM foundations, pgvector persistence, retrieval reranking, safe prompt context, grounding checks, and golden-case AI evaluation are included. See [architecture overview](docs/architecture/system-overview.md) for current LLM/RAG boundaries.


## Phase 11
See [architecture overview](docs/architecture/system-overview.md) and [dependency map](docs/architecture/dependency-map.md) for the retrieval architecture.

## Phase 19 — Vehicle Network Discovery
- Passive multi-bus CAN arbitration-ID profiling
- Periodicity/DLC/payload observation
- Configurable UDS request/response inference
- ECU candidates with confidence and provenance
- Network discovery REST API


## Phase 32 — Clean local AI runtime

The recommended Windows runtime uses standalone `llama-server.exe` on `127.0.0.1:8000` and FastAPI on `127.0.0.1:8001`. The Desktop launcher starts both services automatically. No Ollama runtime and no Python `llama_cpp` binding are required. See [Windows setup](START_HERE_WINDOWS.md) for runtime setup.

## Phase 35
Adaptive llama-server context handling was added. The client reads `/props`, compacts live diagnostic context to fit the actual server limit, and defaults the managed server to 8192 context.


## Windows Desktop icon-preview builder

The clean Windows preview build uses `scripts/build_windows_icon_preview.ps1`
and creates `dist-release/AICarScanner-icon-preview.zip`. The GitHub Actions
`Windows Desktop Icon Preview` workflow is manual-only. This preview validates
icon assets and the executable's native icon, not full app startup or
diagnostic correctness. See [the October 16 audit](docs/testing/repository-audit-2026-10-16.md)
for cleanup decisions and remaining release risks.

## Shared native-client contract

The shared options and workflow are specified in [config/client_contract.json](config/client_contract.json). The backend vehicle catalog is the online source of truth for Desktop, Android, and iOS. Language codes are en, ru, and hy; theme modes are dark and light; diagnostic results use PASS, FAIL, and INCOMPLETE. Platform-specific feature gaps are documented in [PLATFORM_FEATURE_PARITY.md](PLATFORM_FEATURE_PARITY.md).

## Architecture documentation

The implementation is documented from high level to code-level responsibility:

- [Documentation index](docs/README.md)
- [System architecture](docs/architecture/system-overview.md)
- [Domain and diagnostic flow](docs/architecture/domain-and-flow.md)
- [Component hierarchy](docs/architecture/component-hierarchy.md)
- [Dependency map](docs/architecture/dependency-map.md)
- [Architecture visualizations](docs/architecture/visualization.md)

These documents describe the current repository implementation, including the in-process DiagnosticSession registry, database snapshot persistence, deterministic reasoning boundary, RAG/LLM seams, device abstraction, client hierarchy and current architectural risks.
