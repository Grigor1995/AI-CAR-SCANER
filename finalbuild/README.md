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

## Run tests
```bash
pip install -r backend/requirements-dev.txt
pytest -q
```

## Docker
```bash
docker compose up --build
```

## Architecture
See `docs/architecture/phase-1.md`.

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

See `docs/architecture/phase-2.md` for decisions and limitations.

## Phase 4
Professional VCI abstraction is included: device registry/capabilities, adapter lifecycle, generic vendor SDK seam, J2534 Pass-Thru interface, Windows DLL loading seam, VCI simulator and tests.

## Phase 7
Production security and observability foundations are included in `backend/security`, `backend/observability`, and `backend/platform/tenant.py`.

## Phase 9
Real RAG/local LLM foundations, pgvector persistence, retrieval reranking, safe prompt context, grounding checks, and golden-case AI evaluation are included. See `README_PHASE9.md`.


## Phase 11
See `README_PHASE11.md` for persistent pgvector hybrid retrieval and evaluation.

## Phase 19 — Vehicle Network Discovery
- Passive multi-bus CAN arbitration-ID profiling
- Periodicity/DLC/payload observation
- Configurable UDS request/response inference
- ECU candidates with confidence and provenance
- Network discovery REST API


## Phase 32 — Clean local AI runtime

The recommended Windows runtime uses standalone `llama-server.exe` on `127.0.0.1:8000` and FastAPI on `127.0.0.1:8001`. The Desktop launcher starts both services automatically. No Ollama runtime and no Python `llama_cpp` binding are required. See `README_PHASE32.md`.

## Phase 35
Adaptive llama-server context handling was added. The client reads `/props`, compacts live diagnostic context to fit the actual server limit, and defaults the managed server to 8192 context.
