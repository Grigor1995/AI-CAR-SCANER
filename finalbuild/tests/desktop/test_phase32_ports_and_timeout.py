from __future__ import annotations

import importlib
from backend.ai.llm.llama_server import LlamaServerConfig
import apps.desktop.main as desktop_main
from apps.desktop.api_client import DiagnosticApiClient


def test_phase32_default_port_split():
    assert desktop_main.PORT == 8001
    assert desktop_main.LLM_PORT == 8000
    assert DiagnosticApiClient().base_url == "https://ai-car-scaner.onrender.com"
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

    importlib.reload(desktop_main)
