from __future__ import annotations

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
