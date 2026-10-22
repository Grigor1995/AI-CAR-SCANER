from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from apps.desktop.api_client import ApiError, DiagnosticApiClient


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", content=b'{"ok": true}'):
        self.status_code = status_code
        self.ok = 200 <= status_code < 400
        self._payload = payload if payload is not None else {"ok": True}
        self.text = text
        self.content = content

    def json(self):
        return self._payload


@pytest.fixture
def client():
    return DiagnosticApiClient("http://backend.test/", timeout=4)


def test_request_normalizes_base_url_and_sets_timeout(client, monkeypatch):
    response = FakeResponse()
    request = Mock(return_value=response)
    monkeypatch.setattr(client.session, "request", request)

    assert client.health() == {"ok": True}
    request.assert_called_once_with("GET", "http://backend.test/health", timeout=4)


def test_default_backend_uses_local_fastapi_and_short_timeout(monkeypatch):
    monkeypatch.delenv("AI_CAR_BACKEND_URL", raising=False)
    monkeypatch.delenv("AI_CAR_BACKEND_PORT", raising=False)
    client = DiagnosticApiClient()
    assert client.base_url == "http://127.0.0.1:8001"
    assert client.timeout == 8.0



def test_backend_port_is_shared_with_desktop_launcher(monkeypatch):
    monkeypatch.delenv("AI_CAR_BACKEND_URL", raising=False)
    monkeypatch.setenv("AI_CAR_BACKEND_PORT", "8102")
    assert DiagnosticApiClient().base_url == "http://127.0.0.1:8102"


def test_explicit_backend_url_overrides_local_port(monkeypatch):
    monkeypatch.setenv("AI_CAR_BACKEND_PORT", "8102")
    monkeypatch.setenv("AI_CAR_BACKEND_URL", "https://example.test:8443/")
    assert DiagnosticApiClient().base_url == "https://example.test:8443"
    assert DiagnosticApiClient("http://override.test/").base_url == "http://override.test"

def test_empty_response_returns_empty_object(client, monkeypatch):
    monkeypatch.setattr(client.session, "request", Mock(return_value=FakeResponse(content=b"")))
    assert client._request("DELETE", "/resource") == {}


def test_non_json_error_response_is_reported(client, monkeypatch):
    monkeypatch.setattr(client.session, "request", Mock(return_value=FakeResponse(502, text="bad gateway", content=b"bad gateway")))
    with pytest.raises(ApiError, match="HTTP 502: bad gateway"):
        client.health()


def test_json_detail_error_response_is_reported(client, monkeypatch):
    monkeypatch.setattr(client.session, "request", Mock(return_value=FakeResponse(422, payload={"detail": "invalid vehicle"})))
    with pytest.raises(ApiError, match="HTTP 422: invalid vehicle"):
        client.health()


def test_request_exception_is_wrapped(client, monkeypatch):
    monkeypatch.setattr(client.session, "request", Mock(side_effect=requests.ConnectionError("offline")))
    with pytest.raises(ApiError, match="offline") as error:
        client.health()
    assert isinstance(error.value.__cause__, requests.ConnectionError)


@pytest.mark.parametrize(
    ("invoke", "method", "path"),
    [
        (lambda c: c.create_session({"make": "Kia"}), "POST", "/api/v1/sessions"),
        (lambda c: c.vehicle_catalog_entries(), "GET", "/api/v1/vehicle-catalog/entries"),
        (lambda c: c.get_session("s-1"), "GET", "/api/v1/sessions/s-1"),
        (lambda c: c.add_dtc("s-1", "p0302"), "POST", "/api/v1/sessions/s-1/dtcs"),
        (lambda c: c.ingest_evidence("s-1", "shakes on LPG"), "POST", "/api/v1/intelligence/sessions/s-1/evidence/text"),
        (lambda c: c.analyze("s-1"), "POST", "/api/v1/analysis/s-1"),
        (lambda c: c.decision_plan("s-1"), "GET", "/api/v1/decision/sessions/s-1/plan"),
        (lambda c: c.record_test_result("s-1", "t-1", "PASS"), "POST", "/api/v1/intelligence/sessions/s-1/test-results"),
        (lambda c: c.start_simulator("s-1"), "POST", "/api/v1/acquisition/sessions/s-1/start"),
        (lambda c: c.stop_acquisition("s-1"), "POST", "/api/v1/acquisition/sessions/s-1/stop"),
        (lambda c: c.acquisition_status("s-1"), "GET", "/api/v1/acquisition/sessions/s-1/status"),
        (lambda c: c.acquisition_records("s-1", 5000), "GET", "/api/v1/acquisition/sessions/s-1/records"),
        (lambda c: c.telemetry_summary("s-1"), "GET", "/api/v1/telemetry/sessions/s-1/summary"),
        (lambda c: c.analyze_telemetry("s-1"), "POST", "/api/v1/telemetry/sessions/s-1/analyze"),
        (lambda c: c.ai_analyze_live_data("s-1"), "POST", "/api/v1/telemetry/sessions/s-1/ai-analyze-live"),
        (lambda c: c.ai_provider_info(), "GET", "/api/v1/ai/provider"),
        (lambda c: c.network_map("s-1"), "GET", "/api/v1/network-discovery/sessions/s-1/map"),
        (lambda c: c.ingest_can_frames("s-1", "can0", []), "POST", "/api/v1/network-discovery/sessions/s-1/frames"),
        (lambda c: c.active_probe("s-1", ["ecu-1"]), "POST", "/api/v1/network-discovery/sessions/s-1/active-probe"),
        (lambda c: c.active_probe("s-1"), "POST", "/api/v1/network-discovery/sessions/s-1/active-probe"),
        (lambda c: c.list_devices(), "GET", "/api/v1/devices"),
        (lambda c: c.scan_devices("ble"), "POST", "/api/v1/devices/scan/ble"),
        (lambda c: c.probe_wifi("192.0.2.2"), "POST", "/api/v1/devices/wifi/probe"),
        (lambda c: c.add_simulator_device(), "POST", "/api/v1/devices/simulator"),
        (lambda c: c.connect_device("dev-1"), "POST", "/api/v1/devices/dev-1/connect"),
        (lambda c: c.disconnect_device("dev-1"), "POST", "/api/v1/devices/dev-1/disconnect"),
        (lambda c: c.reconnect_device("dev-1"), "POST", "/api/v1/devices/dev-1/reconnect"),
        (lambda c: c.device_status("dev-1"), "GET", "/api/v1/devices/dev-1/status"),
        (lambda c: c.device_vin("dev-1"), "GET", "/api/v1/devices/dev-1/obd/vin"),
        (lambda c: c.device_dtcs("dev-1"), "GET", "/api/v1/devices/dev-1/obd/dtcs"),
        (lambda c: c.device_live_data("dev-1"), "GET", "/api/v1/devices/dev-1/obd/live-data"),
        (lambda c: c.active_map("s-1"), "GET", "/api/v1/network-discovery/sessions/s-1/active-map"),
    ],
)
def test_public_api_methods_route_correctly(client, monkeypatch, invoke, method, path):
    request = Mock(return_value=FakeResponse())
    monkeypatch.setattr(client.session, "request", request)

    invoke(client)

    args, kwargs = request.call_args
    assert args[0] == method
    assert args[1] == "http://backend.test" + path
    assert kwargs["timeout"] == (300.0 if path.endswith("/ai-analyze-live") else 4)
    if path.endswith("/records"):
        assert kwargs["params"] == {"limit": 1000}
    if path.endswith("/ai-analyze-live"):
        assert kwargs["timeout"] == 300.0


def test_shutdown_releases_blocked_http_wait_and_prevents_new_requests(monkeypatch):
    import threading
    import time
    from apps.desktop.api_client import DiagnosticApiClient, ApiError
    client = DiagnosticApiClient(timeout=300)
    entered = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    errors = []
    def blocked(*args, **kwargs):
        entered.set()
        release.wait(5)
        raise RuntimeError("late response")
    monkeypatch.setattr(client.session, "request", blocked)
    def caller():
        try:
            client.health()
        except ApiError as exc:
            errors.append(str(exc))
        finally:
            finished.set()
    thread = threading.Thread(target=caller)
    thread.start()
    try:
        assert entered.wait(1)
        started = time.monotonic()
        client.cancel_pending()
        assert finished.wait(1)
        assert time.monotonic() - started < 1
        assert errors == ["Application is closing"]
        with pytest.raises(ApiError, match="closing"):
            client.health()
    finally:
        release.set()
        thread.join(2)
