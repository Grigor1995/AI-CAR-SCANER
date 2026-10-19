"""Negative API contract tests: entirely mocked, no external services."""
from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from apps.desktop.api_client import ApiError, DiagnosticApiClient


class ResponseStub:
    def __init__(self, status: int, payload=None, text: str = "API unavailable", invalid_json=False):
        self.status_code = status
        self.ok = 200 <= status < 400
        self.content = b"{not-json}" if invalid_json else b'{"response": true}'
        self.text = text
        self.payload = payload
        self.invalid_json = invalid_json

    def json(self):
        if self.invalid_json:
            raise ValueError("bad JSON from API")
        return self.payload


@pytest.fixture
def api():
    return DiagnosticApiClient("http://mock-api.invalid", timeout=2)


@pytest.mark.parametrize(
    ("http_status", "detail"),
    [
        (400, "invalid request"),
        (401, "token expired"),
        (403, "forbidden"),
        (404, "unknown session"),
        (408, "request timeout"),
        (409, "concurrent update"),
        (422, "invalid measurements"),
        (429, "rate limited"),
        (500, "unexpected server error"),
        (502, "bad gateway"),
        (503, "service unavailable"),
        (504, "gateway timeout"),
    ],
)
def test_negative_http_status_is_never_reported_as_success(api, http_status, detail):
    api.session.request = Mock(return_value=ResponseStub(http_status, {"detail": detail}))
    with pytest.raises(ApiError, match=rf"HTTP {http_status}: {detail}"):
        api.health()


@pytest.mark.parametrize("payload", [["unexpected", "list"], "backend failed", 42, None])
def test_negative_non_object_error_body_does_not_raise_attribute_error(api, payload):
    api.session.request = Mock(return_value=ResponseStub(503, payload=payload, text="gateway failure"))
    with pytest.raises(ApiError, match="HTTP 503: gateway failure"):
        api.health()


def test_negative_html_error_body_falls_back_to_server_text(api):
    api.session.request = Mock(
        return_value=ResponseStub(502, text="<html>Bad Gateway</html>", invalid_json=True)
    )
    with pytest.raises(ApiError, match="HTTP 502: <html>Bad Gateway</html>"):
        api.health()


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (requests.ConnectTimeout("connection timed out"), "Cannot connect to FastAPI"),
        (requests.ReadTimeout("slow backend"), "did not respond within 2 seconds"),
        (requests.ConnectionError("connection refused"), "connection failed"),
        (requests.exceptions.SSLError("invalid certificate"), "connection failed"),
        (requests.RequestException("connection interrupted"), "API request failed"),
    ],
)
def test_negative_network_errors_become_user_facing_api_errors(api, failure, expected):
    api.session.request = Mock(side_effect=failure)
    with pytest.raises(ApiError, match=expected) as exception:
        api.health()
    assert exception.value.__cause__ is failure


def test_negative_malformed_success_payload_raises_controlled_api_error(api):
    api.session.request = Mock(return_value=ResponseStub(200, invalid_json=True))
    with pytest.raises(ApiError, match="returned invalid JSON") as exception:
        api.health()
    assert isinstance(exception.value.__cause__, ValueError)


@pytest.mark.parametrize("language", ["en", "ru", "hy", "EN", "de", "", None])
def test_language_parameter_has_safe_fallback(api, language):
    api.session.request = Mock(return_value=ResponseStub(200, payload={}))
    api.analyze("session-1", language=language)
    assert api.session.request.call_args.kwargs["params"] == {
        "language": language if language in {"en", "ru", "hy"} else "en"
    }


@pytest.mark.parametrize("requested_limit,expected_limit", [(0, 1), (-100, 1), (1, 1), (1000, 1000), (1001, 1000), (999999, 1000)])
def test_negative_record_limit_is_clamped(api, requested_limit, expected_limit):
    api.session.request = Mock(return_value=ResponseStub(200, payload={}))
    api.acquisition_records("session-1", requested_limit)
    assert api.session.request.call_args.kwargs["params"] == {"limit": expected_limit}


def test_negative_connection_failure_cannot_create_session(api):
    call = Mock(side_effect=requests.ConnectionError("offline"))
    api.session.request = call
    with pytest.raises(ApiError, match="connection failed"):
        api.create_session({"make": "Mercedes-Benz", "model": "E-Class"})
    assert call.call_count == 1


@pytest.mark.parametrize("status", [400, 404, 409, 422, 500, 503])
def test_negative_result_submission_does_not_mask_backend_failure(api, status):
    api.session.request = Mock(return_value=ResponseStub(status, {"detail": "rejected"}))
    with pytest.raises(ApiError, match=f"HTTP {status}: rejected"):
        api.record_test_result("session-1", "check-1", "FAIL", notes="measured")
