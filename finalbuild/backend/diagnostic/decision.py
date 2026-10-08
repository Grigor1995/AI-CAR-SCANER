from __future__ import annotations

from dataclasses import dataclass, field
from math import log2
from typing import Iterable
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .models import DiagnosticSession, DiagnosticTest, EvidenceStatus, SessionState


class DecisionCandidate(BaseModel):
    test_id: UUID
    name: str
    purpose: str
    priority_score: float = Field(ge=0, le=1)
    information_gain: float = Field(ge=0, le=1)
    evidence_fit: float = Field(ge=0, le=1)
    cost_penalty: float = Field(ge=0, le=1)
    risk_penalty: float = Field(ge=0, le=1)
    rationale: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    prerequisite_gaps: list[str] = Field(default_factory=list)


class DiagnosticDecisionPlan(BaseModel):
    session_id: UUID
    state: SessionState
    selected_test_id: UUID | None = None
    candidates: list[DecisionCandidate] = Field(default_factory=list)
    stop_reasons: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class TestSpec:
    name: str
    purpose: str
    target_hypotheses: tuple[str, ...]
    required_evidence: tuple[str, ...] = ()
    cost: float = 2.0
    risk: float = 1.0
    safety_notes: tuple[str, ...] = ()


CATALOG: tuple[TestSpec, ...] = (
    TestSpec(
        "Compare fuel-trim and misfire behavior by fuel mode",
        "Separate fuel-system-specific behavior from a general ignition/load problem.",
        ("LPG injection", "LPG calibration", "ignition under LPG load"),
        ("fuel_mode_lpg", "petrol normal"),
        cost=1.0,
        risk=1.0,
        safety_notes=("Perform on a secure vehicle with appropriate workshop precautions.",),
    ),
    TestSpec(
        "Inspect LPG pressure and injector behavior under load",
        "Check whether gas delivery remains stable during the reported RPM/load window.",
        ("LPG injection", "LPG calibration"),
        ("fuel_mode_lpg",),
        cost=2.0,
        risk=2.0,
        safety_notes=("Follow LPG system manufacturer procedures; avoid leaks and ignition sources.",),
    ),
    TestSpec(
        "Check ignition performance under LPG load",
        "Determine whether elevated ignition demand under LPG load correlates with the symptom.",
        ("ignition", "ignition under LPG load", "load-dependent combustion"),
        ("misfire", "fuel_mode_lpg"),
        cost=2.0,
        risk=2.0,
        safety_notes=("Use insulated/properly rated test equipment and follow workshop ignition-safety procedures.",),
    ),
    TestSpec(
        "Inspect intake system for an air leak",
        "Check for unmetered air that could become more apparent under the reported operating condition.",
        ("intake", "load-dependent combustion"),
        ("misfire",),
        cost=2.0,
        risk=1.0,
        safety_notes=("Use the approved leak-test procedure and protect hot/electrical components.",),
    ),
    TestSpec(
        "Compare cylinder-specific misfire counters and compression evidence",
        "Determine whether the event is cylinder-specific and whether mechanical evidence is present.",
        ("ignition", "intake", "load-dependent combustion"),
        ("misfire",),
        cost=3.0,
        risk=2.0,
        safety_notes=("Compression testing requires proper engine shutdown and manufacturer procedures.",),
    ),
)


class DiagnosticDecisionEngine:
    """Selects the next diagnostic test using information value, evidence fit, cost and safety."""

    def __init__(self, catalog: Iterable[TestSpec] = CATALOG):
        self.catalog = tuple(catalog)

    def build_plan(self, session: DiagnosticSession, limit: int = 5) -> DiagnosticDecisionPlan:
        active_hypotheses = [h for h in session.hypotheses if not h.status.startswith("rejected")]
        categories = {h.category for h in active_hypotheses}
        if not categories:
            return DiagnosticDecisionPlan(
                session_id=session.session_id,
                state=session.state,
                stop_reasons=["No diagnostic hypotheses are available yet; run initial analysis first."],
            )

        results_by_name = {self._recommendation_key(r.name) for r in session.recommendations}
        completed_ids = {str(r.test_id) for r in session.test_results}
        # Rule analysis can regenerate DiagnosticTest UUIDs on every pass.
        # Therefore completion must also be tracked by the stable test name,
        # otherwise a just-completed recommendation can immediately reappear
        # with a new UUID after re-analysis.
        completed_names = {
            self._recommendation_key(r.test_name)
            for r in session.test_results
            if r.test_name
        }
        existing_recommendation_ids = {self._recommendation_key(r.name): r.id for r in session.recommendations}
        evidence_text = " ".join(e.fact.lower() for e in session.evidence)

        candidates: list[DecisionCandidate] = []
        for spec in self.catalog:
            matched = [c for c in spec.target_hypotheses if c in categories]
            gaps = [req for req in spec.required_evidence if req.lower() not in evidence_text]
            if not matched:
                continue
            existing_id = existing_recommendation_ids.get(self._recommendation_key(spec.name))
            if self._recommendation_key(spec.name) in completed_names:
                continue
            if self._recommendation_key(spec.name) in results_by_name and existing_id and str(existing_id) in completed_ids:
                continue

            n = max(len(categories), 1)
            target_n = len(set(matched))
            p = min(max(target_n / n, 0.0), 1.0)
            entropy = 0.0 if p in (0.0, 1.0) else -(p * log2(p) + (1-p) * log2(1-p))
            # A diagnostic test still has useful value when it targets a
            # single active hypothesis; avoid exposing a misleading 0.00.
            information_gain = round(0.25 + 0.75 * entropy, 4)

            fit = len(spec.required_evidence) - len(gaps)
            evidence_fit = fit / max(len(spec.required_evidence), 1)
            cost_penalty = min(max((spec.cost - 1.0) / 4.0, 0.0), 1.0)
            risk_penalty = min(max((spec.risk - 1.0) / 4.0, 0.0), 1.0)
            prerequisite_penalty = 0.15 if gaps else 0.0

            score = (
                0.50 * information_gain
                + 0.20 * evidence_fit
                + 0.15 * (1 - cost_penalty)
                + 0.15 * (1 - risk_penalty)
                - prerequisite_penalty
            )
            score = min(max(score, 0.0), 1.0)

            diagnostic_test = DiagnosticTest(
                id=existing_id or uuid4(),
                name=spec.name,
                purpose=spec.purpose,
                safety_notes=list(spec.safety_notes),
                priority_score=round(score, 4),
                expected_information_gain=round(information_gain, 4),
                estimated_cost=spec.cost,
                risk_level=self._risk_label(spec.risk),
                prerequisites=list(spec.required_evidence),
                target_hypotheses=list(spec.target_hypotheses),
            )
            rationale = [
                f"Targets {', '.join(matched)}.",
                f"Estimated information gain: {information_gain:.2f}.",
            ]
            if gaps:
                rationale.append(f"Missing evidence: {', '.join(gaps)}.")
            else:
                rationale.append("Required evidence is present.")

            candidates.append(
                DecisionCandidate(
                    test_id=diagnostic_test.id,
                    name=diagnostic_test.name,
                    purpose=diagnostic_test.purpose,
                    priority_score=diagnostic_test.priority_score,
                    information_gain=diagnostic_test.expected_information_gain,
                    evidence_fit=round(evidence_fit, 4),
                    cost_penalty=round(cost_penalty, 4),
                    risk_penalty=round(risk_penalty, 4),
                    rationale=rationale,
                    safety_notes=list(spec.safety_notes),
                    prerequisite_gaps=gaps,
                )
            )

        candidates.sort(key=lambda c: (-c.priority_score, c.risk_penalty, c.cost_penalty, c.name))
        selected = candidates[0].test_id if candidates else None
        stop_reasons: list[str] = []
        if not candidates:
            stop_reasons.append("No unused diagnostic test has sufficient expected value for the current hypotheses.")
        return DiagnosticDecisionPlan(
            session_id=session.session_id,
            state=session.state,
            selected_test_id=selected,
            candidates=candidates[:limit],
            stop_reasons=stop_reasons,
        )

    def refresh_recommendations(self, session: DiagnosticSession) -> DiagnosticDecisionPlan:
        plan = self.build_plan(session)
        previous = {self._recommendation_key(x.name): x for x in session.recommendations}
        session.recommendations = []
        catalog_by_name = {x.name: x for x in self.catalog}
        for candidate in plan.candidates:
            spec = catalog_by_name.get(candidate.name)
            if spec is None:
                continue
            prior = previous.get(self._recommendation_key(spec.name))
            session.recommendations.append(
                DiagnosticTest(
                    id=prior.id if prior else candidate.test_id,
                    name=spec.name,
                    purpose=spec.purpose,
                    safety_notes=list(spec.safety_notes),
                    priority_score=candidate.priority_score,
                    expected_information_gain=candidate.information_gain,
                    estimated_cost=spec.cost,
                    risk_level=self._risk_label(spec.risk),
                    prerequisites=list(spec.required_evidence),
                    target_hypotheses=list(spec.target_hypotheses),
                )
            )
        session.audit_log.append({
            "event": "DECISION_PLAN_UPDATED",
            "selected_test_id": str(plan.selected_test_id) if plan.selected_test_id else None,
            "candidate_count": len(plan.candidates),
        })
        return plan

    def enrich_external_recommendations(
        self,
        session: DiagnosticSession,
        recommendations: Iterable[DiagnosticTest],
    ) -> list[DiagnosticTest]:
        """Fill decision metadata for rule-generated tests not present in the catalog."""
        categories = {
            h.category for h in session.hypotheses
            if not h.status.startswith("rejected")
        }
        category_count = max(len(categories), 1)
        enriched: list[DiagnosticTest] = []

        from math import log2

        for item in recommendations:
            target_matches = len(set(item.target_hypotheses) & categories)
            coverage = target_matches / category_count if category_count else 0.0
            if target_matches == 0:
                information_gain = 0.15
            elif 0.0 < coverage < 1.0:
                entropy = -(coverage * log2(coverage) + (1.0 - coverage) * log2(1.0 - coverage))
                information_gain = max(0.25, entropy)
            else:
                information_gain = 0.25

            item.expected_information_gain = round(min(information_gain, 0.95), 4)
            if item.estimated_cost <= 0:
                item.estimated_cost = {
                    "LOW": 1.0,
                    "MEDIUM": 2.0,
                    "HIGH": 4.0,
                }.get(item.risk_level.upper(), 1.0)
            if item.priority_score <= 0:
                item.priority_score = round(min(
                    0.65 * item.expected_information_gain
                    + 0.35 * (
                        1.0 if item.risk_level.upper() == "LOW"
                        else 0.75 if item.risk_level.upper() == "MEDIUM"
                        else 0.5
                    ),
                    1.0,
                ), 4)
            enriched.append(item)

        return enriched

    def update_hypotheses_from_result(self, session: DiagnosticSession, test: DiagnosticTest | None, result: str) -> list[str]:
        if test is None:
            return []
        text = result.strip().lower()
        supported: list[str] = []
        # Normalize the UI outcome values as well as free-form technician notes.
        # PASS means the selected test did NOT show the targeted fault;
        # FAIL means the targeted fault was observed.
        positive = (
            text in {"fail", "failed", "failure"}
            or any(k in text for k in ("supports", "confirmed", "drops", "low", "unstable", "leak", "misfire reproduced", "fails"))
        )
        negative = (
            text in {"pass", "passed", "normal", "stable", "within spec", "no leak"}
            or any(k in text for k in ("normal", "stable", "no leak", "within spec", "passes"))
        )
        for hypothesis in session.hypotheses:
            if hypothesis.category not in test.target_hypotheses:
                continue
            if positive and not negative:
                hypothesis.status = "supported_by_test"
                supported.append(hypothesis.category)
            elif negative and not positive:
                hypothesis.status = "disfavored_by_test"
        return supported

    @staticmethod
    def _recommendation_key(name: str) -> str:
        return " ".join(name.lower().split())

    @staticmethod
    def _risk_label(risk: float) -> str:
        if risk >= 4:
            return "HIGH"
        if risk >= 2.5:
            return "MEDIUM"
        return "LOW"
