"""Real HTTP integration contract for the Desktop client, served locally.

No external backend/OBD/LLM. Covers the diagnostic path plus negative HTTP
responses through actual requests.Session networking, not just monkeypatches.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from urllib.parse import urlsplit, parse_qs

import pytest

from apps.desktop.api_client import ApiError, DiagnosticApiClient


@pytest.fixture
def local_api():
    events = []
    state = {"reject_result": False, "unavailable": False}

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, body):
            raw = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            parsed = urlsplit(self.path)
            events.append(("GET", parsed.path, parse_qs(parsed.query), None))
            if parsed.path == "/health":
                self.respond(503 if state["unavailable"] else 200, {"status": "down" if state["unavailable"] else "ok"})
            elif parsed.path == "/api/v1/decision/sessions/demo-1/plan":
                self.respond(200, {"tests": [{"id": "t-1", "name": "LPG pressure test"}]})
            elif parsed.path == "/api/v1/devices":
                self.respond(200, {"devices": []})
            else:
                self.respond(404, {"detail": "not found"})

        def do_POST(self):
            parsed = urlsplit(self.path)
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size).decode("utf-8") or "{}")
            events.append(("POST", parsed.path, parse_qs(parsed.query), payload))
            if parsed.path == "/api/v1/sessions":
                self.respond(201, {"session_id": "demo-1", "state": "COLLECTING"})
            elif parsed.path == "/api/v1/sessions/demo-1/dtcs":
                self.respond(201, {"dtcs": [{"code": payload["code"]}]})
            elif parsed.path == "/api/v1/intelligence/sessions/demo-1/evidence/text":
                self.respond(201, {"evidence": [{"text": payload["text"]}]})
            elif parsed.path == "/api/v1/analysis/demo-1":
                self.respond(200, {"state": "ANALYSIS_READY", "hypotheses": [{"status": "possible"}]})
            elif parsed.path == "/api/v1/intelligence/sessions/demo-1/test-results":
                if state["reject_result"]:
                    self.respond(422, {"detail": "invalid test result"})
                else:
                    self.respond(200, {"result": payload["result"], "status": "RECORDED"})
            else:
                self.respond(404, {"detail": "unknown session"})

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        client = DiagnosticApiClient(f"http://127.0.0.1:{server.server_port}", timeout=3)
        yield client, events, state
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_real_http_complete_manual_diagnostic_and_test_result(local_api):
    client, events, _state = local_api
    assert client.health()["status"] == "ok"
    session = client.create_session({"make": "Mercedes-Benz", "model": "E-Class", "year": 2006})
    assert session["session_id"] == "demo-1"
    assert client.add_dtc("demo-1", "P0302")["dtcs"][0]["code"] == "P0302"
    assert "LPG" in client.ingest_evidence("demo-1", "LPG misfire under 2000 RPM")["evidence"][0]["text"]
    assert client.analyze("demo-1", language="hy")["hypotheses"][0]["status"] == "possible"
    assert client.decision_plan("demo-1")["tests"][0]["id"] == "t-1"
    assert client.record_test_result("demo-1", "t-1", "INCOMPLETE", notes="not measured", language="ru")["result"] == "INCOMPLETE"
    assert [event[1] for event in events] == [
        "/health", "/api/v1/sessions", "/api/v1/sessions/demo-1/dtcs",
        "/api/v1/intelligence/sessions/demo-1/evidence/text",
        "/api/v1/analysis/demo-1", "/api/v1/decision/sessions/demo-1/plan",
        "/api/v1/intelligence/sessions/demo-1/test-results",
    ]
    assert events[-1][2] == {"language": ["ru"]}
    assert events[4][2] == {"language": ["hy"]}


def test_real_http_rejected_test_result_never_becomes_pass(local_api):
    client, events, state = local_api
    state["reject_result"] = True
    with pytest.raises(ApiError, match="HTTP 422: invalid test result"):
        client.record_test_result("demo-1", "missing-test", "PASS")
    assert events[-1][3]["result"] == "PASS"


def test_real_http_offline_status_is_controlled_error(local_api):
    client, _events, state = local_api
    state["unavailable"] = True
    with pytest.raises(ApiError, match="HTTP 503"):
        client.health()


def test_real_http_unknown_session_fails_explicitly(local_api):
    client, _events, _state = local_api
    with pytest.raises(ApiError, match="HTTP 404: unknown session"):
        client.add_dtc("no-such-session", "P0302")
