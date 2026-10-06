from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


def main() -> None:
    base = os.getenv("LOCAL_LLM_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
    payload = json.dumps({
        "model": os.getenv("LOCAL_LLM_SERVER_MODEL", "Qwen3-8B-Q4_K_M.gguf"),
        "messages": [{"role": "user", "content": "Reply with exactly: LOCAL AI OK"}],
        "temperature": 0,
        "max_tokens": 32,
        "stream": False,
    }).encode("utf-8")
    request = Request(
        f"{base}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        result = json.loads(response.read().decode("utf-8"))
    text = str(result["choices"][0]["message"]["content"]).strip()
    print(text)
    if "LOCAL AI OK" not in text:
        raise SystemExit("Unexpected local AI response")
    print("PASS")


if __name__ == "__main__":
    main()
