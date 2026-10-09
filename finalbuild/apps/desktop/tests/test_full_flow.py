from __future__ import annotations

from unittest.mock import Mock

from apps.desktop.api_client import ApiError, DiagnosticApiClient


class Response:
    def __init__(self, payload: dict, status_code: int = 200):
        self.status_code = status_code
        self.ok = 200 <= status_code < 400
        self.content = __import__("json").dumps(payload).encode()
        self.text = self.content.decode()

    def json(self):
        return __import__("json").loads(self.content)


def test_diagnostic_happy_path_sends_expected_payloads_and_order():
    client = DiagnosticApiClient("http://backend.test")
    responses = [
        Response({"session_id": "s-1", "state": "COLLECTING"}),
        Response({"session_id": "s-1", "dtcs": [{"code": "P0302"}]}),
        Response({"session_id": "s-1", "evidence": [{"fact": "LPG only"}]}),
        Response({"session_id": "s-1", "state": "ANALYSIS_READY", "hypotheses": [{"status": "possible"}]}),
        Response({"session_id": "s-1", "tests": [{"id": "t-1"}]}),
        Response({"session_id": "s-1", "test_results": [{"test_id": "t-1", "result": "PASS"}]}),
    ]
    request = Mock(side_effect=responses)
    client.session.request = request

    created = client.create_session({"make": "Mercedes-Benz", "model": "W211 E350", "year": 2006})
    dtcs = client.add_dtc("s-1", "P0302")
    evidence = client.ingest_evidence("s-1", "Misfire only on LPG below 2000 RPM")
    analysis = client.analyze("s-1")
    plan = client.decision_plan("s-1")
    result = client.record_test_result("s-1", "t-1", "PASS", {"pressure_bar": 1.2}, "verified")

    assert created["session_id"] == "s-1"
    assert dtcs["dtcs"][0]["code"] == "P0302"
    assert evidence["evidence"][0]["fact"] == "LPG only"
    assert analysis["hypotheses"][0]["status"] == "possible"
    assert plan["tests"][0]["id"] == "t-1"
    assert result["test_results"][0]["result"] == "PASS"
    assert [call.args[1] for call in request.call_args_list] == [
        "http://backend.test/api/v1/sessions",
        "http://backend.test/api/v1/sessions/s-1/dtcs",
        "http://backend.test/api/v1/intelligence/sessions/s-1/evidence/text",
        "http://backend.test/api/v1/intelligence/sessions/s-1/analyze",
        "http://backend.test/api/v1/decision/sessions/s-1/plan",
        "http://backend.test/api/v1/intelligence/sessions/s-1/test-results",
    ]
    assert request.call_args_list[0].kwargs["json"]["year"] == 2006
    assert request.call_args_list[1].kwargs["json"]["code"] == "P0302"
    assert request.call_args_list[2].kwargs["json"]["text"].startswith("Misfire only")
    assert request.call_args_list[5].kwargs["json"] == {
        "test_id": "t-1",
        "result": "PASS",
        "measurements": {"pressure_bar": 1.2},
        "notes": "verified",
    }


def test_diagnostic_flow_surfaces_backend_not_found_without_fake_success():
    client = DiagnosticApiClient("http://backend.test")
    client.session.request = Mock(return_value=Response({"detail": "session not found"}, 404))

    try:
        client.analyze("missing-session")
    except ApiError as exc:
        assert str(exc) == "HTTP 404: session not found"
    else:
        raise AssertionError("Expected ApiError for unknown session")
