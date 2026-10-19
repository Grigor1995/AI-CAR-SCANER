"""Phase 3: real Desktop client -> real FastAPI -> reasoning/decision E2E.

No internet, physical OBD adapter, LLM, or external HTTP server is involved.
Unlike mocked UI-only flows, every request exercises real FastAPI routes and
the diagnostic reasoning engine using an in-process TestClient transport.
"""
from __future__ import annotations

from urllib.parse import urlsplit
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from api.main import app
from apps.desktop.api_client import ApiError, DiagnosticApiClient


VEHICLE = {
    "make": "Mercedes-Benz",
    "model": "W211 E350",
    "chassis": "W211",
    "year": 2006,
    "engine": "M272 3.5",
    "fuel": ["petrol", "LPG"],
    "ecu": "ME9.7",
}
SYMPTOM = (
    "Engine misfires and shakes on LPG below 2000 RPM under acceleration/load; "
    "petrol normal, running smoothly on petrol. Cylinder 2 P0302."
)
EXPECTED_DOMAINS = {
    "LPG fuel delivery / mixture",
    "ignition / combustion",
    "air-fuel / intake",
}
FORBIDDEN_CONCLUSIONS = (
    "confirmed coil failure",
    "definitely the ignition coil",
    "ignition coil is confirmed faulty",
)


class _CompatibleResponse:
    """Provide requests.Response-like properties for httpx/TestClient output."""

    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code
        self.ok = 200 <= response.status_code < 400
        self.content = response.content
        self.text = response.text

    def json(self):
        return self._response.json()


@pytest.fixture
def desktop_with_real_backend(monkeypatch):
    """Desktop API client talking to REAL FastAPI handlers, not fake JSON."""

    server = TestClient(app)
    desktop = DiagnosticApiClient("http://desktop-e2e.invalid", timeout=4)
    calls = []

    def transport(method, url, **kwargs):
        parsed = urlsplit(url)
        # Fail closed: never allow a test to access Render or another service.
        assert parsed.scheme == "http" and parsed.netloc == "desktop-e2e.invalid"
        assert "timeout" in kwargs
        assert "timeout" not in (parsed.query or "")
        request_kwargs = {key: value for key, value in kwargs.items() if key != "timeout"}
        response = server.request(
            method, parsed.path + (("?" + parsed.query) if parsed.query else ""),
            **request_kwargs,
        )
        calls.append((method, parsed.path, response.status_code))
        return _CompatibleResponse(response)

    monkeypatch.setattr(desktop.session, "request", transport)
    try:
        yield desktop, calls
    finally:
        desktop.session.close()
        server.close()


def _assert_no_unproven_hardware_diagnosis(payload):
    hypotheses = payload.get("hypotheses", [])
    assert hypotheses, "The engine must return testable hypotheses"
    # A P0302 DTC + LPG symptoms must never independently confirm a coil.
    assert all(not str(h["status"]).lower().startswith("confirmed") for h in hypotheses)
    statements = " ".join(str(h.get("statement", "")).lower() for h in hypotheses)
    for unsupported in FORBIDDEN_CONCLUSIONS:
        assert unsupported not in statements


@pytest.mark.parametrize(
    ("language", "outcome"),
    [("en", "FAIL"), ("hy", "INCOMPLETE"), ("ru", "PASS")],
)
def test_w211_real_api_full_diagnostic_result_reanalysis_and_persistence(
    desktop_with_real_backend, language, outcome
):
    desktop, calls = desktop_with_real_backend

    created = desktop.create_session(VEHICLE)
    session_id = created["session_id"]
    UUID(session_id)

    ingested = desktop.ingest_evidence(session_id, SYMPTOM)
    assert ingested["evidence"], "Manual evidence must be retained"
    with_dtc = desktop.add_dtc(session_id, "P0302")
    assert any(d["code"] == "P0302" for d in with_dtc["dtcs"])

    initial = desktop.analyze(session_id, language="en")
    categories = {h["category"] for h in initial["hypotheses"]}
    assert EXPECTED_DOMAINS.issubset(categories)
    _assert_no_unproven_hardware_diagnosis(initial)
    assert initial["recommendations"]
    assert all(r["priority_score"] > 0 for r in initial["recommendations"])
    assert all(r["expected_information_gain"] > 0 for r in initial["recommendations"])
    assert all(r["estimated_cost"] > 0 for r in initial["recommendations"])

    # Decision endpoint must surface runnable candidates and stable UUIDs.
    before = desktop.decision_plan(session_id)
    assert before["candidates"], "Missing test candidates after initial analysis"
    selected = before["candidates"][0]
    selected_id = selected["test_id"]
    UUID(selected_id)
    assert selected["name"]

    measured = desktop.record_test_result(
        session_id,
        selected_id,
        outcome,
        {"rpm": 1800, "fuel_mode": "LPG"},
        "Measured under identical load; result is not a component verdict.",
        language=language,
    )
    assert measured["test_results"]
    _assert_no_unproven_hardware_diagnosis(measured)

    # Mirror Desktop UI: submit result, request another analysis, load next plan.
    followup = desktop.analyze(session_id, language="en")
    next_plan = desktop.decision_plan(session_id)
    _assert_no_unproven_hardware_diagnosis(followup)
    assert all(
        c["name"] != selected["name"] for c in next_plan["candidates"]
    ), "Completed diagnostic test was suggested again after re-analysis"

    # Cross-language UI presentations must not alter canonical stored status.
    persisted = desktop.get_session(session_id)
    assert persisted["vehicle"]["year"] == 2006
    assert any(d["code"] == "P0302" for d in persisted["dtcs"])
    assert any(r["test_id"] == selected_id and r["result"] == outcome
               for r in persisted["test_results"])
    assert any(e.get("fact") for e in persisted["evidence"])
    assert any(path.endswith("/test-results") and status == 200
               for _method, path, status in calls)


def test_negative_real_backend_rejects_unknown_session_and_invalid_result(
    desktop_with_real_backend
):
    desktop, calls = desktop_with_real_backend

    with pytest.raises(ApiError, match="HTTP 404"):
        desktop.analyze("00000000-0000-0000-0000-000000000001")

    created = desktop.create_session(VEHICLE)
    session_id = created["session_id"]
    with pytest.raises(ApiError, match="HTTP 422"):
        desktop.record_test_result(
            session_id, "00000000-0000-0000-0000-000000000001", "SKIPPED"
        )
    # Even a correctly named result is invalid with a malformed test UUID.
    with pytest.raises(ApiError, match="HTTP 422"):
        desktop.record_test_result(session_id, "not-a-uuid", "PASS")

    persisted = desktop.get_session(session_id)
    assert persisted["test_results"] == []
    assert any(code == 422 for _method, _path, code in calls)


def test_negative_real_backend_requires_analysis_before_decision_candidates(
    desktop_with_real_backend
):
    desktop, _calls = desktop_with_real_backend

    session_id = desktop.create_session(VEHICLE)["session_id"]
    plan = desktop.decision_plan(session_id)
    assert not plan["candidates"]
    assert plan["stop_reasons"]
