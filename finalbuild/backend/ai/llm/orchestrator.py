from __future__ import annotations
import json
from ai.interfaces import LLMProvider, LLMResponse
from diagnostic.models import DiagnosticSession

class DiagnosticLLMOrchestrator:
    """LLM is constrained to explanation/orchestration; deterministic reasoning remains authoritative."""
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def build_context(self, session: DiagnosticSession, retrieved: list[dict] | None = None) -> dict:
        return {
            "session_id": str(session.session_id),
            "vehicle": session.vehicle.model_dump() if session.vehicle else None,
            "evidence": [e.model_dump(mode="json") for e in session.evidence],
            "hypotheses": [h.model_dump(mode="json") for h in session.hypotheses],
            "recommended_tests": [t.model_dump(mode="json") for t in session.recommendations],
            "retrieved_knowledge": retrieved or [],
            "instruction": "Do not invent measurements, confirmations, or component failures. Separate evidence from inference.",
        }

    async def explain(self, session: DiagnosticSession, retrieved: list[dict] | None = None) -> LLMResponse:
        context = self.build_context(session, retrieved)
        prompt = "Explain the current diagnostic reasoning using only the supplied evidence and clearly label uncertainty."
        return await self.provider.generate(prompt, context)
