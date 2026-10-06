# Phase 11 — Real Vector Indexing & Hybrid Retrieval

Phase 11 makes the knowledge retrieval layer persistent and database-backed.

## Pipeline

`Query -> deterministic rewrite -> embeddings -> pgvector ANN search -> PostgreSQL lexical search -> weighted fusion -> downstream reranker/LLM context`

## PostgreSQL

The `rag_chunks` table stores chunk content, metadata, embeddings and a generated `tsvector` column. GIN indexes support metadata/full-text filtering. HNSW is the default ANN index; IVFFlat can be selected through configuration.

## Scope filtering

Retrieval accepts metadata filters such as manufacturer, model, year, engine, ECU, fuel, language and document_type. The goal is to prevent unrelated vehicle knowledge from entering the diagnostic context.

## Query rewriting

The first query is always preserved. A second deterministic expansion may add automotive aliases (for example LPG/autogas or O2/oxygen sensor/lambda). Rewriting never creates vehicle-specific claims.

## Fusion

Vector and lexical candidates are normalized and combined with configurable weights. The current default is 65% vector / 35% lexical.

## Evaluation gate

`RetrievalEvaluator` supports recall@k-style golden cases and required-term checks. Retrieval regressions should block an AI/RAG release when expected relevant documents disappear or required grounding terms are absent.

## Production configuration

Environment variables:
- `DATABASE_URL`
- `RAG_EMBEDDING_DIMENSIONS`
- `RAG_VECTOR_INDEX` (`hnsw` or `ivfflat`)
- `RAG_HNSW_M`
- `RAG_HNSW_EF_CONSTRUCTION`
- `RAG_IVFFLAT_LISTS`

## Next hardening

Replace the deterministic hash embedding with a production sentence-transformer or other approved embedding service/model, add reciprocal-rank fusion/cross-encoder evaluation, and run the repository against a real pgvector CI service.
