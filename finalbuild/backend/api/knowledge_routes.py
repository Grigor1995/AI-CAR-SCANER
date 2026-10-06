from __future__ import annotations
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ai.ingestion.models import DocumentMetadata
from ai.ingestion.pipeline import KnowledgeIngestionPipeline

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge-ingestion"])
pipeline = KnowledgeIngestionPipeline()

class IngestTextRequest(BaseModel):
    title: str
    text: str
    metadata: dict = {}

@router.post("/ingest/text")
def ingest_text(request: IngestTextRequest):
    metadata = DocumentMetadata(**request.metadata)
    with NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=True) as tmp:
        tmp.write(request.text)
        tmp.flush()
        result = pipeline.ingest_file(tmp.name, metadata, request.title)
    return {
        "document": result.document.__dict__,
        "chunks": [c.__dict__ for c in result.chunks],
        "warnings": list(result.warnings),
    }

@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...), metadata_json: str = Form("{}"), title: str | None = Form(None)):
    try:
        metadata = DocumentMetadata(**__import__('json').loads(metadata_json))
    except Exception as exc:
        raise HTTPException(400, f"Invalid metadata JSON: {exc}") from exc
    suffix = Path(file.filename or "upload.txt").suffix or ".txt"
    data = await file.read()
    with NamedTemporaryFile("wb", suffix=suffix, delete=True) as tmp:
        tmp.write(data); tmp.flush()
        result = pipeline.ingest_file(tmp.name, metadata, title or Path(file.filename or "upload").stem)
    return {"document": result.document.__dict__, "chunks": [c.__dict__ for c in result.chunks], "warnings": list(result.warnings)}
