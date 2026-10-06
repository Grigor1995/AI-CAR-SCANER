# Phase 8 — Diagnostic Intelligence

Phase 8 turns the existing diagnostic domain into an evidence-driven reasoning loop.

## Pipeline

```text
Natural language / OBD / CAN / UDS / technician measurement
                         |
                         v
              Structured Evidence
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
     Rules             ML/Signals        RAG
        |                |                |
        +----------------+----------------+
                         |
                         v
              Diagnostic Intelligence
                         |
              +----------+----------+
              |          |          |
              v          v          v
          Questions     Tests    Hypotheses
              |          |          |
              +----------+----------+
                         |
                         v
                   Test Result
                         |
                         v
                    Re-analysis
```

## Design rules

1. Every extracted fact keeps provenance and status.
2. Rules and measurements remain deterministic sources of diagnostic truth.
3. ML identifies signal anomalies; it does not automatically name a failed component.
4. RAG provides source-grounded context with metadata filters.
5. The LLM is an explanation/orchestration layer, not an authority to invent measurements or confirmations.
6. The reasoning loop can continue after a test result is recorded.

## Current implementation

- `backend/ai/reasoning/evidence_extractor.py`: conservative structured extraction.
- `backend/ai/reasoning/engine.py`: orchestration loop around deterministic rules.
- `backend/ai/ml/anomaly.py`: dependency-free numerical anomaly baseline.
- `backend/ai/rag/store.py`: local lexical hybrid-RAG foundation with metadata filters.
- `backend/ai/rag/evaluator.py`: retrieval regression evaluator.
- `backend/ai/llm/orchestrator.py`: constrained LLM context/prompt orchestration.
- `backend/api/intelligence_routes.py`: evidence ingestion, analysis and test-result endpoints.

## Production extensions

Next implementations should add persistent pgvector ingestion, real embedding providers, reranking, model registry/versioning, feature stores, calibrated confidence models, asynchronous inference queues, human-in-the-loop review, and AI safety gates.
