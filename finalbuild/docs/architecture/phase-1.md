# Phase 1 Architecture Decision

**Decision:** modular monolith backend (FastAPI/Pydantic/SQLAlchemy/PostgreSQL+pgvector), shared Flutter clients, platform-independent diagnostic domain, hardware behind adapters.

**Why:** minimizes duplicated diagnostic logic and operational complexity while preserving hardware independence and future extraction boundaries.

**Alternatives:** microservices (deferred); vendor-specific VCI coupling (rejected); LLM-first diagnosis (rejected because evidence provenance must remain authoritative).

**Trade-offs:** disciplined module boundaries are required; native platform plugins remain necessary for hardware; local AI depends on device resources.

**MVP boundary:** no ECU programming/writing; no proprietary reverse engineering; no paid cloud LLM dependency; no real vehicle required for automated tests.
