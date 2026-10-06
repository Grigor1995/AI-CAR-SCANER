from __future__ import annotations
from collections import defaultdict
from diagnostic.models import DiagnosticSession, EvidenceStatus, EvidenceSource, Hypothesis, DiagnosticTest, SessionState
from diagnostic.rules import DiagnosticReasoningEngine
from backend.ai.reasoning.evidence_extractor import StructuredEvidenceExtractor
from backend.ai.ml.anomaly import NumericAnomalyDetector
from backend.diagnostic.decision import DiagnosticDecisionEngine

class DiagnosticIntelligenceEngine:
    """Evidence-driven loop around the deterministic domain engine."""
    def __init__(self):
        self.extractor = StructuredEvidenceExtractor()
        self.rules = DiagnosticReasoningEngine()
        self.anomaly = NumericAnomalyDetector()
        self.decision = DiagnosticDecisionEngine()

    def ingest_text(self, session: DiagnosticSession, text: str, source: EvidenceSource = EvidenceSource.USER_REPORTED) -> DiagnosticSession:
        session.evidence.extend(self.extractor.extract(text, source))
        session.state = SessionState.SYMPTOMS_COLLECTED
        return session

    def normalize_existing(self, session: DiagnosticSession) -> DiagnosticSession:
        existing = {e.fact for e in session.evidence}
        for symptom in session.symptoms:
            for e in self.extractor.from_symptom(symptom):
                if e.fact not in existing:
                    session.evidence.append(e)
                    existing.add(e.fact)
        for dtc in session.dtcs:
            e = self.extractor.from_dtc(dtc)
            if e.fact not in existing:
                session.evidence.append(e); existing.add(e.fact)
        return session

    def analyze(self, session: DiagnosticSession) -> DiagnosticSession:
        self.normalize_existing(session)
        self.rules.analyze(session)
        self._annotate_scores(session)
        self._add_missing_questions(session)
        session.state = SessionState.QUESTIONS_PENDING if session.audit_log and session.audit_log[-1].get("event") == "QUESTIONS_IDENTIFIED" else SessionState.INITIAL_ANALYSIS
        self.decision.refresh_recommendations(session)
        if session.recommendations:
            session.state = SessionState.TESTING
        elif any(x.get("event") == "QUESTIONS_IDENTIFIED" for x in session.audit_log[-3:]):
            session.state = SessionState.QUESTIONS_PENDING
        else:
            session.state = SessionState.INITIAL_ANALYSIS
        session.audit_log.append({"event": "INTELLIGENCE_ANALYSIS_COMPLETED", "evidence_count": len(session.evidence), "hypothesis_count": len(session.hypotheses)})
        return session

    def record_test_result(self, session: DiagnosticSession, test_id, result: str, measurements: dict | None = None, notes: str | None = None) -> DiagnosticSession:
        from backend.diagnostic.models import TestResult, Evidence
        measurements = measurements or {}
        session.test_results.append(TestResult(test_id=test_id, result=result, measurements=measurements, notes=notes))
        session.evidence.append(Evidence(
            fact=f"Test {test_id} result: {result}", source=EvidenceSource.TECHNICIAN_OBSERVED,
            status=EvidenceStatus.MEASURED, confidence=0.95, metadata={"test_id": str(test_id), "measurements": measurements}
        ))
        selected_test = next((x for x in session.recommendations if x.id == test_id), None)
        self.decision.update_hypotheses_from_result(session, selected_test, result)
        analyzed = self.analyze(session)
        # Re-apply the test interpretation after re-analysis so regenerated hypotheses retain the measured-result effect.
        supported = self.decision.update_hypotheses_from_result(analyzed, selected_test, result)
        analyzed.audit_log.append({"event": "TEST_RESULT_INTERPRETED", "test_id": str(test_id), "supported_hypotheses": supported})
        analyzed.state = SessionState.HYPOTHESIS_VALIDATION
        return analyzed

    def next_test(self, session: DiagnosticSession) -> DiagnosticTest | None:
        return session.recommendations[0] if session.recommendations else None

    def _annotate_scores(self, session: DiagnosticSession) -> None:
        text = " ".join(e.fact.lower() for e in session.evidence)
        for h in session.hypotheses:
            score = 0.25
            category = h.category.lower()
            if category in text:
                score += 0.10
            if category in {"lpg injection", "lpg fuel delivery", "lpg calibration"} and "lpg" in text:
                score += 0.25
            if category == "ignition under lpg load" and "misfire" in text and "lpg" in text:
                score += 0.22
            if category == "lean mixture" and any(x in text for x in ("lean", "fuel trim", "p0171", "p0174")):
                score += 0.25
            if category == "rich mixture" and any(x in text for x in ("rich", "p0172", "p0175")):
                score += 0.25
            if category == "air metering / maf" and any(x in text for x in ("maf", "p0101", "airflow")):
                score += 0.25
            if category == "catalyst efficiency" and any(x in text for x in ("p0420", "p0430", "catalyst")):
                score += 0.25
            if category == "cam/crank correlation" and any(x in text for x in ("p0016", "p0017", "p0018", "p0019", "timing")):
                score += 0.25
            if category == "transmission control / gear ratio" and any(x in text for x in ("p0730", "gear", "transmission", "slip")):
                score += 0.25
            if category == "vehicle network communication" and any(x in text for x in ("u0100", "u0121", "can", "communication")):
                score += 0.25
            h.status = f"possible:{min(score, 0.95):.2f}"

    def _add_missing_questions(self, session: DiagnosticSession) -> None:
        text = " ".join(e.fact.lower() for e in session.evidence)
        questions = []
        if "lpg" in text and "gas pressure" not in text:
            questions.append("What is LPG gas pressure at idle and during the reported load/RPM window?")
        if "misfire" in text and not any("fuel trim" in e.fact.lower() for e in session.evidence):
            questions.append("What are STFT/LTFT values on petrol versus LPG at idle and under load?")
        if not questions:
            return
        session.audit_log.append({"event": "QUESTIONS_IDENTIFIED", "questions": questions})
