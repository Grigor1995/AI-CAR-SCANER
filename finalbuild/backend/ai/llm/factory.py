from __future__ import annotations

import os

from backend.ai.interfaces import LocalLLMProvider
from backend.ai.llm.llama_server import LlamaServerConfig, LlamaServerLLMProvider
from backend.ai.llm.openai_compatible import OpenAICompatibleConfig, HttpOpenAICompatibleProvider


def build_llm_provider():
    provider = os.getenv("DIAGNOSTIC_LLM_PROVIDER", "llama-server").lower()
    if provider in {"llama-server", "llama_server", "llamaserver", "local"}:
        return LlamaServerLLMProvider(LlamaServerConfig.from_env())
    if provider in {"openai-compatible", "openai_compatible"}:
        return HttpOpenAICompatibleProvider(OpenAICompatibleConfig(
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:8001"),
            model=os.getenv("LLM_MODEL", "local-model"),
            api_key=os.getenv("LLM_API_KEY"),
        ))
    if provider == "placeholder":
        return LocalLLMProvider()
    raise ValueError(f"Unsupported LLM provider: {provider}")
