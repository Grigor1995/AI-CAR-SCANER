from __future__ import annotations
from typing import Any
import os
import requests

class ApiError(RuntimeError):
    pass

class DiagnosticApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 8.0) -> None:
        # Match the launcher's local port when no explicit API URL is supplied.
        # Desktop and API client must not silently connect to different servers.
        default_url = f"http://127.0.0.1:{os.environ.get('AI_CAR_BACKEND_PORT', '8001')}"
        self.base_url = (base_url or os.environ.get("AI_CAR_BACKEND_URL") or default_url).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            request_timeout = kwargs.pop("timeout", self.timeout)
            response = self.session.request(method, self.base_url + path, timeout=request_timeout, **kwargs)
        except requests.ConnectTimeout as exc:
            raise ApiError(
                f"Cannot connect to FastAPI at {self.base_url}. Check that the backend is running "
                "and AI_CAR_BACKEND_URL points to the correct host."
            ) from exc
        except requests.ReadTimeout as exc:
            raise ApiError(
                f"FastAPI at {self.base_url} did not respond within {request_timeout} seconds."
            ) from exc
        except requests.ConnectionError as exc:
            raise ApiError(
                f"FastAPI connection failed at {self.base_url}: {exc}. "
                "Start the backend or set AI_CAR_BACKEND_URL to a reachable API URL."
            ) from exc
        except requests.RequestException as exc:
            raise ApiError(f"API request failed: {exc}") from exc
        if not response.ok:
            try:
                body = response.json()
                detail = body.get("detail", response.text) if isinstance(body, dict) else response.text
            except ValueError:
                detail = response.text
            raise ApiError(f"HTTP {response.status_code}: {detail}")
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError(
                f"FastAPI at {self.base_url} returned invalid JSON for {method} {path}."
            ) from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def create_session(self, vehicle: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/sessions", json=vehicle)

    def vehicle_catalog_entries(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/vehicle-catalog/entries")

    # Presentation clients all consume this same backend authoritative registry.
    def registry_makes(self, query: str = "") -> list[str]:
        return self._request("GET", "/api/v1/vehicle-registry/makes", params={"q": query})

    def registry_models(self, make: str, year: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"make": make}
        if year is not None:
            params["year"] = year
        return self._request("GET", "/api/v1/vehicle-registry/models", params=params)

    def registry_fitments(self, make: str, model: str, year: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"make": make, "model": model}
        if year is not None:
            params["year"] = year
        return self._request("GET", "/api/v1/vehicle-registry/fitments", params=params)

    def obd_protocol_hints(self, year: int, market: str = "unknown",
                           make: str = "", detected_elm: str | None = None) -> dict[str, Any]:
        return self._request("GET", "/api/v1/vehicle-registry/compatibility",
                             params={"year": year, "market": market, "make": make,
                                     **({"detected_elm": detected_elm} if detected_elm else {})})

    def registry_photo(self, make: str, model: str, chassis: str = "") -> dict[str, Any]:
        return self._request("GET", "/api/v1/vehicle-registry/photo",
                             params={"make": make, "model": model, "chassis": chassis})


    def get_session(self, session_id: str, language: str | None = None) -> dict[str, Any]:
        kwargs = {"params": {"language": language}} if language else {}
        return self._request("GET", f"/api/v1/sessions/{session_id}", **kwargs)

    def update_vehicle(self, session_id: str, vehicle: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", f"/api/v1/sessions/{session_id}/vehicle", json=vehicle)

    def add_dtc(self, session_id: str, code: str, description: str = "") -> dict[str, Any]:
        return self._request("POST", f"/api/v1/sessions/{session_id}/dtcs", json={"code": code, "description": description, "source": "USER_REPORTED"})

    def ingest_evidence(self, session_id: str, text: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/intelligence/sessions/{session_id}/evidence/text", json={"text": text})

    def analyze(self, session_id: str, language: str = "en") -> dict[str, Any]:
        normalized_language = language if language in {"en", "ru", "hy"} else "en"
        return self._request(
            "POST", f"/api/v1/analysis/{session_id}",
            params={"language": normalized_language},
        )

    def decision_plan(self, session_id: str, language: str | None = None) -> dict[str, Any]:
        kwargs = {"params": {"language": language}} if language else {}
        return self._request("GET", f"/api/v1/decision/sessions/{session_id}/plan", **kwargs)

    def record_test_result(
        self,
        session_id: str,
        test_id: str,
        result: str,
        measurements: dict[str, Any] | None = None,
        notes: str = "",
        language: str = "en",
    ) -> dict[str, Any]:
        normalized_language = language if language in {"en", "ru", "hy"} else "en"
        return self._request(
            "POST",
            f"/api/v1/intelligence/sessions/{session_id}/test-results",
            params={"language": normalized_language},
            json={"test_id": test_id, "result": result, "measurements": measurements or {}, "notes": notes},
        )

    def start_bound_acquisition(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/acquisition/sessions/{session_id}/start", json={"adapter": "bound"})

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

    def ai_analyze_live_data(self, session_id: str, language: str = "en") -> dict[str, Any]:
        return self._request("POST", f"/api/v1/telemetry/sessions/{session_id}/ai-analyze-live", params={"language": language}, timeout=float(os.environ.get("AI_CAR_LIVE_AI_TIMEOUT_S", "300")))

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

    def list_sessions(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/sessions")

    def ingest_reference(self, title: str, text: str) -> dict[str, Any]:
        return self._request("POST", "/api/v1/knowledge/ingest/text", json={
            "title": title, "text": text,
            "metadata": {"source": "user-reported-repair", "document_type": "repair_note"},
        })
