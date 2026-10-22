from __future__ import annotations
import json
from diagnostic.models import DiagnosticSession, EvidenceStatus, EvidenceSource, DiagnosticTest, SessionState
from diagnostic.rules import DiagnosticReasoningEngine
from ai.reasoning.evidence_extractor import StructuredEvidenceExtractor
from ai.ml.anomaly import NumericAnomalyDetector
from diagnostic.decision import DiagnosticDecisionEngine

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
        rule_recommendations = list(session.recommendations)
        self.decision.refresh_recommendations(session)
        if not session.recommendations and rule_recommendations:
            session.recommendations = self._fallback_recommendations(
                session, rule_recommendations
            )
        if session.recommendations:
            session.state = SessionState.TESTING
        elif any(x.get("event") == "QUESTIONS_IDENTIFIED" for x in session.audit_log[-3:]):
            session.state = SessionState.QUESTIONS_PENDING
        else:
            session.state = SessionState.INITIAL_ANALYSIS
        session.audit_log.append({"event": "INTELLIGENCE_ANALYSIS_COMPLETED", "evidence_count": len(session.evidence), "hypothesis_count": len(session.hypotheses)})
        return session

    def record_test_result(self, session: DiagnosticSession, test_id, result: str, measurements: dict | None = None, notes: str | None = None) -> DiagnosticSession:
        from diagnostic.models import TestResult, Evidence
        measurements = measurements or {}
        normalized_result = result.strip().upper()
        selected_test = next(
            (x for x in session.recommendations if str(x.id) == str(test_id)),
            None,
        )
        session.test_results.append(TestResult(
            test_id=test_id,
            result=normalized_result,
            measurements=measurements,
            notes=notes,
            test_name=selected_test.name if selected_test else None,
        ))
        evidence_parts = [
            f"Completed diagnostic test: {selected_test.name}" if selected_test else f"Completed diagnostic test ID: {test_id}",
            f"result: {normalized_result}",
        ]
        if notes and notes.strip():
            evidence_parts.append(f"technician notes: {notes.strip()}")
        if measurements:
            evidence_parts.append(
                "measurements: " + json.dumps(measurements, ensure_ascii=False, sort_keys=True, default=str)
            )
        session.evidence.append(Evidence(
            fact="; ".join(evidence_parts),
            source=EvidenceSource.TECHNICIAN_OBSERVED,
            status=EvidenceStatus.MEASURED,
            confidence=0.95,
            metadata={"test_id": str(test_id), "test_name": selected_test.name if selected_test else None, "result": normalized_result, "measurements": measurements, "notes": notes},
        ))
        # Free-form technician notes are part of the result evidence. This lets
        # entries such as "pressure drops" or "no leak, stable" affect the
        # targeted hypotheses even when the UI outcome is left inconclusive.
        interpretation_text = " ".join(x for x in (normalized_result, notes or "") if x)
        self.decision.update_hypotheses_from_result(session, selected_test, interpretation_text)
        analyzed = self.analyze(session)
        # Re-apply the test interpretation after rules regenerate the hypothesis
        # objects, then rebuild the plan once more so remaining-test priorities
        # reflect the latest PASS/FAIL evidence instead of stale pre-result scores.
        supported = self.decision.update_hypotheses_from_result(analyzed, selected_test, interpretation_text)
        previous_remaining = list(analyzed.recommendations)
        self.decision.refresh_recommendations(analyzed)
        if not analyzed.recommendations and previous_remaining:
            analyzed.recommendations = self._fallback_recommendations(analyzed, previous_remaining)
        analyzed.audit_log.append({"event": "TEST_RESULT_INTERPRETED", "test_id": str(test_id), "supported_hypotheses": supported})
        analyzed.state = SessionState.HYPOTHESIS_VALIDATION
        return analyzed

    def _fallback_recommendations(
        self, session: DiagnosticSession, candidates: list[DiagnosticTest]
    ) -> list[DiagnosticTest]:
        """Keep rule-generated tests, but never reintroduce a completed test by name.

        Rule analysis creates fresh UUIDs on each pass, so UUID-only filtering can
        accidentally resurrect a test that was already recorded. Stable names are
        the fallback identity for completed tests.
        """
        latest_ids = {str(item.test_id): item.result for item in session.test_results}
        latest_names = {self.decision._recommendation_key(item.test_name): item.result for item in session.test_results if item.test_name}
        completed_ids = {key for key, result in latest_ids.items() if result in {"PASS", "FAIL"}}
        completed_names = {key for key, result in latest_names.items() if result in {"PASS", "FAIL"}}
        remaining = [
            item for item in candidates
            if str(item.id) not in completed_ids
            and self.decision._recommendation_key(item.name) not in completed_names
        ]
        enriched = self.decision.enrich_external_recommendations(session, remaining)
        return sorted(
            enriched,
            key=lambda item: (
                -item.priority_score,
                {"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get(item.risk_level.upper(), 3),
                item.estimated_cost,
                item.name,
            ),
        )

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
