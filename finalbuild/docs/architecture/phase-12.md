# Phase 12 Architecture — Embeddings, Reranking and Quality Gates

## Retrieval stack

```text
Query
  |
  +--> Query Rewriter
  |
  +--> Local Embedding Model
  |       |
  |       +--> pgvector HNSW
  |
  +--> PostgreSQL lexical search
            |
            +--> Hybrid Fusion
                    |
                    +--> Candidate Pool
                            |
                            +--> Cross-Encoder Reranker
                                    |
                                    +--> Top-K Evidence
```

## Provider abstraction

The diagnostic platform can run with:

- offline deterministic embeddings for tests
- sentence-transformers for local semantic embeddings
- fastembed/ONNX-oriented CPU embeddings
- lexical reranking fallback
- local cross-encoder reranking

The rest of the diagnostic engine does not depend on a specific model.

## Quality evaluation

Each golden query records:

- expected document IDs
- optional graded relevance
- required grounding terms

The evaluator computes:

- Recall@K — relevant coverage
- MRR — first relevant result position
- NDCG@K — graded ranking quality

A release gate can require minimum thresholds for all three metrics.

## Model migration safety

Embedding models define the vector dimension and semantic space. Model changes therefore require:

1. a new model/version identifier;
2. a coordinated index rebuild;
3. re-evaluation against the golden dataset;
4. comparison against the previous baseline;
5. only then promotion to production.
