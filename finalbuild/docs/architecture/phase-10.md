# Phase 10 — Production Knowledge Ingestion Pipeline

Phase 10 turns technical knowledge ingestion into a deterministic, auditable pipeline.

## Flow

```text
PDF / TXT / Markdown / HTML / JSON / YAML
                |
                v
          Parser Registry
                |
                v
        Normalization / Hash
                |
                v
       Document Metadata Gate
                |
                v
       Heading-aware Chunking
                |
                v
      Provenance + Page Ranges
                |
                v
       Embedding / Vector Index
                |
                v
         Hybrid RAG Retrieval
```

## Supported input types

- PDF (text extraction via `pypdf`)
- TXT / Markdown / reStructuredText
- HTML
- JSON / YAML

Scanned PDFs without a text layer are reported as empty rather than silently indexed. OCR can be introduced as a separate, licensed preprocessing service later.

## Metadata isolation

Every chunk inherits metadata such as manufacturer, model, year, engine, ECU, fuel, document type, source, version, language and license. Retrieval can therefore restrict context to the relevant vehicle scope rather than mixing unrelated manuals.

## Deduplication

Documents are content-hashed with SHA-256. The generated document identifier is deterministic for a given source path and content hash. Chunk identifiers are deterministic as well, enabling idempotent indexing and regression comparisons.

## Retrieval regression data

The dataset builder extracts DTC codes from ingested documents and creates reviewable query → relevant chunk examples. These cases can be committed to `datasets/rag-regression/` and evaluated whenever chunking, embedding, retrieval or model configuration changes.

## Production boundary

The ingestion pipeline intentionally does not make licensing assumptions. `license` and `source` are first-class metadata and downstream policy should reject documents that are not authorized for storage or retrieval.
