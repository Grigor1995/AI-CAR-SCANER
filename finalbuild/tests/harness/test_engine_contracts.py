import pytest
from uuid import uuid4

from ai.reasoning.engine import DiagnosticIntelligenceEngine
from diagnostic.models import (
    DTC,
    DiagnosticSession,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    Symptom,
    Vehicle,
)


def _session(text: str = "Engine shakes on LPG below 2000 RPM under load; petrol is normal.", dtc: str = "P0302"):
    return DiagnosticSession(
        vehicle=Vehicle(
            make="Mercedes-Benz",
            model="W211 E350",
            year=2006,
            engine="M272 3.5",
            fuel=["petrol", "LPG"],
            ecu="ME 9.7",
        ),
        symptoms=[Symptom(raw_text=text)],
        dtcs=[DTC(code=dtc)],
    )


def test_normalize_existing_is_idempotent():
    engine = DiagnosticIntelligenceEngine()
    session = _session()
    engine.normalize_existing(session)
    first = len(session.evidence)
    engine.normalize_existing(session)
    assert len(session.evidence) == first


def test_ingest_text_changes_state_and_records_evidence():
    engine = DiagnosticIntelligenceEngine()
    session = DiagnosticSession()
    engine.ingest_text(session, "LPG misfire under load", EvidenceSource.TECHNICIAN_OBSERVED)
    assert session.state.value == "SYMPTOMS_COLLECTED"
    assert session.evidence


def test_analyze_identifies_missing_lpg_questions():
    result = DiagnosticIntelligenceEngine().analyze(_session())
    assert result.audit_log
    assert any(x.get("event") == "QUESTIONS_IDENTIFIED" for x in result.audit_log)
    assert result.recommendations
    assert result.state.value == "TESTING"


def test_analyze_without_questions_stays_initial_or_testing():
    session = DiagnosticSession(vehicle=Vehicle(make="Toyota", model="Camry"))
    result = DiagnosticIntelligenceEngine().analyze(session)
    assert result.state.value in {"INITIAL_ANALYSIS", "TESTING"}


def test_record_test_result_adds_measured_evidence_and_interprets_result():
    engine = DiagnosticIntelligenceEngine()
    session = engine.analyze(_session())
    test = engine.next_test(session)
    assert test is not None
    result = engine.record_test_result(
        session,
        test.id,
        "PASS",
        measurements={"pressure_kpa": 110},
        notes="pressure stable",
    )
    assert result.test_results[-1].result == "PASS"
    assert result.test_results[-1].test_name == test.name
    assert any(e.status == EvidenceStatus.MEASURED for e in result.evidence)
    assert result.state.value == "HYPOTHESIS_VALIDATION"
    assert any(x.get("event") == "TEST_RESULT_INTERPRETED" for x in result.audit_log)


def test_record_test_result_handles_unknown_test():
    engine = DiagnosticIntelligenceEngine()
    session = _session()
    result = engine.record_test_result(session, uuid4(), "INCOMPLETE", notes="not enough data")
    assert result.test_results[-1].test_name is None
    assert result.test_results[-1].result == "INCOMPLETE"


@pytest.mark.parametrize(
    "text,dtc,expected",
    [
        ("Fuel trim is lean and idle is rough", "P0171", "lean mixture"),
        ("Rich mixture under load", "P0172", "rich mixture"),
        ("MAF airflow is implausible", "P0101", "air metering / maf"),
        ("Catalyst efficiency is low", "P0420", "catalyst efficiency"),
        ("Cam timing correlation fault", "P0016", "cam/crank correlation"),
        ("Transmission gear ratio error and slip", "P0730", "transmission control / gear ratio"),
        ("CAN communication fault", "U0100", "vehicle network communication"),
    ],
)
def test_score_annotations_cover_major_diagnostic_domains(text, dtc, expected):
    session = _session(text, dtc)
    result = DiagnosticIntelligenceEngine().analyze(session)
    matching = [h for h in result.hypotheses if h.category.lower() == expected]
    assert matching
    assert all(h.status.startswith("possible:") for h in matching)
