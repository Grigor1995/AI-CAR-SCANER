# Phase 9 — Real RAG, Local LLM and AI Evaluation

Phase 9 turns the Phase 8 diagnostic-intelligence foundation into a provider-based AI stack.

## Components
- Ollama local LLM provider
- OpenAI-compatible HTTP provider for self-hosted/local servers
- Deterministic offline embedding provider for tests and fallback
- pgvector persistence adapter
- lexical reranker baseline with a replaceable interface point
- safe prompt-context builder derived only from DiagnosticSession evidence
- grounding evaluator
- golden-case evaluator with forbidden-claim gates

## Design rules
1. The deterministic diagnostic engine remains authoritative for evidence, tests and hypotheses.
2. LLM output is explanatory/orchestration only.
3. A component is not considered confirmed unless explicit evidence has CONFIRMED status.
4. Vehicle metadata should be used as retrieval filters when available.
5. Every retrieval result carries document metadata for provenance.
6. Offline/dev operation does not require a paid API.

## Local stack
```text
FastAPI
  -> DiagnosticIntelligencePipeline
       -> deterministic reasoning
       -> retrieval/reranking
       -> SafePromptContext
       -> Ollama / local OpenAI-compatible endpoint

PostgreSQL + pgvector
  -> knowledge chunks + embeddings
```

## Example environment
```text
DIAGNOSTIC_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

For a self-hosted OpenAI-compatible server:
```text
DIAGNOSTIC_LLM_PROVIDER=openai-compatible
LLM_BASE_URL=http://localhost:8001
LLM_MODEL=local-model
```

## Evaluation gates
- retrieval hit rate
- grounding / unsupported-claim detection
- expected diagnostic category coverage
- forbidden-confirmation checks
- deterministic repeatability for regression cases

Production deployment should add a semantic embedding model, ANN indexes, a cross-encoder reranker, prompt-version tracking, model-version tracking, and human review workflows.
