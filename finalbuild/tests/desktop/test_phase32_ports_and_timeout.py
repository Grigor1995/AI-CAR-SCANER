from __future__ import annotations

import importlib
from backend.ai.llm.llama_server import LlamaServerConfig
import apps.desktop.main as desktop_main
from apps.desktop.api_client import DiagnosticApiClient


def test_phase32_default_port_split(monkeypatch):
    # The API client default must be deterministic even when the developer's
    # shell exports a custom URL for running the application locally/remotely.
    monkeypatch.delenv("AI_CAR_BACKEND_URL", raising=False)

    assert desktop_main.PORT == 8001
    assert desktop_main.LLM_PORT == 8000
    assert DiagnosticApiClient().base_url == "http://127.0.0.1:8001"
    assert LlamaServerConfig.from_env().base_url == "http://127.0.0.1:8000"


def test_phase32_ai_timeout_defaults():
    assert LlamaServerConfig.from_env().timeout_s >= 300



def test_phase32_custom_backend_port_updates_default_url(monkeypatch):
    with monkeypatch.context() as env:
        env.setenv("AI_CAR_BACKEND_HOST", "127.0.0.1")
        env.setenv("AI_CAR_BACKEND_PORT", "8002")
        env.delenv("AI_CAR_BACKEND_URL", raising=False)

        reloaded = importlib.reload(desktop_main)
        assert reloaded.PORT == 8002
        assert reloaded.BACKEND_URL == "http://127.0.0.1:8002"
        assert DiagnosticApiClient().base_url == reloaded.BACKEND_URL

    importlib.reload(desktop_main)


def test_exact_local_url_port_matches_launcher(monkeypatch):
    with monkeypatch.context() as env:
        env.setenv("AI_CAR_BACKEND_URL", "http://127.0.0.1:8123")
        env.delenv("AI_CAR_BACKEND_PORT", raising=False)
        importlib.reload(desktop_main)
        assert desktop_main.LOCAL_BACKEND is True
        assert desktop_main.PORT == 8123
        assert desktop_main.HEALTH_URL == "http://127.0.0.1:8123/health"
        assert DiagnosticApiClient().base_url == desktop_main.BACKEND_URL
    importlib.reload(desktop_main)


def test_localhost_prefix_does_not_match_remote_hostname(monkeypatch):
    with monkeypatch.context() as env:
        env.setenv("AI_CAR_BACKEND_URL", "http://localhost.example.com:8123")
        importlib.reload(desktop_main)
        assert desktop_main.LOCAL_BACKEND is False
    importlib.reload(desktop_main)
