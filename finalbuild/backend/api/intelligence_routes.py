from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from diagnostic.models import EvidenceSource, TestResult
from backend.ai.reasoning.engine import DiagnosticIntelligenceEngine
from api.state import sessions

router = APIRouter(prefix="/api/v1/intelligence", tags=["diagnostic-intelligence"])
engine = DiagnosticIntelligenceEngine()

class IngestTextRequest(BaseModel):
    text: str
    source: EvidenceSource = EvidenceSource.USER_REPORTED

class TestResultRequest(BaseModel):
    test_id: UUID
    result: str
    measurements: dict = {}
    notes: str | None = None

@router.post("/sessions/{session_id}/evidence/text")
def ingest_text(session_id: str, request: IngestTextRequest):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    return engine.ingest_text(sessions[session_id], request.text, request.source)

@router.post("/sessions/{session_id}/analyze")
def analyze(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    return engine.analyze(sessions[session_id])

@router.post("/sessions/{session_id}/test-results")
def add_test_result(session_id: str, request: TestResultRequest):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    return engine.record_test_result(sessions[session_id], request.test_id, request.result, request.measurements, request.notes)
