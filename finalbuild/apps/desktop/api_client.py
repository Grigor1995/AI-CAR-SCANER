from __future__ import annotations
from typing import Any
import os
import requests

class ApiError(RuntimeError):
    pass

class DiagnosticApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = (base_url or os.environ.get("AI_CAR_BACKEND_URL", "http://127.0.0.1:8001")).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            request_timeout = kwargs.pop("timeout", self.timeout)
            response = self.session.request(method, self.base_url + path, timeout=request_timeout, **kwargs)
        except requests.RequestException as exc:
            raise ApiError(str(exc)) from exc
        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(f"HTTP {response.status_code}: {detail}")
        if not response.content:
            return {}
        return response.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def create_session(self, vehicle: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/sessions", json=vehicle)

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/sessions/{session_id}")

    def add_dtc(self, session_id: str, code: str, description: str = "") -> dict[str, Any]:
        return self._request("POST", f"/api/v1/sessions/{session_id}/dtcs", json={"code": code, "description": description, "source": "USER_REPORTED"})

    def ingest_evidence(self, session_id: str, text: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/intelligence/sessions/{session_id}/evidence/text", json={"text": text})

    def analyze(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/intelligence/sessions/{session_id}/analyze")

    def decision_plan(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/decision/sessions/{session_id}/plan")

    def record_test_result(self, session_id: str, test_id: str, result: str, measurements: dict[str, Any] | None = None, notes: str = "") -> dict[str, Any]:
        return self._request("POST", f"/api/v1/intelligence/sessions/{session_id}/test-results", json={"test_id": test_id, "result": result, "measurements": measurements or {}, "notes": notes})

    def start_simulator(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/acquisition/sessions/{session_id}/start", json={"adapter": "simulator"})

    def stop_acquisition(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/acquisition/sessions/{session_id}/stop")

    def acquisition_status(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/acquisition/sessions/{session_id}/status")

    def acquisition_records(self, session_id: str, limit: int = 300) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/acquisition/sessions/{session_id}/records", params={"limit": min(max(limit, 1), 1000)})

    def telemetry_summary(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/telemetry/sessions/{session_id}/summary")

    def analyze_telemetry(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/telemetry/sessions/{session_id}/analyze")

    def ai_analyze_live_data(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/telemetry/sessions/{session_id}/ai-analyze-live", timeout=float(os.environ.get("AI_CAR_LIVE_AI_TIMEOUT_S", "300")))

    def ai_provider_info(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/ai/provider")

    def network_map(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/network-discovery/sessions/{session_id}/map")

    def ingest_can_frames(self, session_id: str, bus: str, frames: list[dict[str, Any]]) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/network-discovery/sessions/{session_id}/frames", json={"bus": bus, "frames": frames})

    def active_probe(self, session_id: str, candidate_ids: list[str] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if candidate_ids:
            payload["candidate_ids"] = candidate_ids
        return self._request("POST", f"/api/v1/network-discovery/sessions/{session_id}/active-probe", json=payload)

    def list_devices(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/devices")

    def scan_devices(self, transport: str, timeout: float = 3.0) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/devices/scan/{transport}", json={"timeout": timeout})

    def probe_wifi(self, host: str, port: int = 35000, timeout: float = 2.0) -> dict[str, Any]:
        return self._request("POST", "/api/v1/devices/wifi/probe", json={"host": host, "port": port, "timeout": timeout})

    def add_simulator_device(self) -> dict[str, Any]:
        return self._request("POST", "/api/v1/devices/simulator")

    def connect_device(self, device_id: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/devices/{device_id}/connect", json={"config": config or {}})

    def disconnect_device(self, device_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/devices/{device_id}/disconnect")

    def reconnect_device(self, device_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/devices/{device_id}/reconnect")

    def device_status(self, device_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/devices/{device_id}/status")

    def device_vin(self, device_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/devices/{device_id}/obd/vin")

    def device_dtcs(self, device_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/devices/{device_id}/obd/dtcs")

    def device_live_data(self, device_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/devices/{device_id}/obd/live-data")

    def active_map(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/network-discovery/sessions/{session_id}/active-map")
