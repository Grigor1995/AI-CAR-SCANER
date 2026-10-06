from __future__ import annotations
import json
from dataclasses import dataclass
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from backend.ai.interfaces import LLMProvider, LLMResponse

@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    model: str
    api_key: str | None = None
    timeout_s: float = 60.0
    temperature: float = 0.1

class HttpOpenAICompatibleProvider(LLMProvider):
    """Works with OpenAI-compatible local/self-hosted endpoints."""
    def __init__(self, config: OpenAICompatibleConfig):
        self.config = config

    async def generate(self, prompt: str, context: dict) -> LLMResponse:
        messages = [
            {"role": "system", "content": "Use only supplied diagnostic evidence and retrieved sources. Do not invent facts."},
            {"role": "user", "content": json.dumps({"task": prompt, "context": context}, ensure_ascii=False)},
        ]
        payload = {"model": self.config.model, "messages": messages, "temperature": self.config.temperature}
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        req = Request(f"{self.config.base_url.rstrip('/')}/v1/chat/completions", data=json.dumps(payload).encode(), headers=headers, method="POST")
        try:
            with urlopen(req, timeout=self.config.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI-compatible inference failed: {exc}") from exc
        text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(text, self.config.model, "openai-compatible", raw=body)
