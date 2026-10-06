from __future__ import annotations

import json
import sys
import urllib.request

base = "http://127.0.0.1:8000"
print("Testing llama-server at", base)

with urllib.request.urlopen(base + "/health", timeout=5) as response:
    health = json.loads(response.read().decode("utf-8"))
print("health:", health)

with urllib.request.urlopen(base + "/v1/models", timeout=5) as response:
    models = json.loads(response.read().decode("utf-8"))
print("models:", [x.get("id") for x in models.get("data", [])])

payload = json.dumps({
    "model": "Qwen3-8B-Q4_K_M.gguf",
    "messages": [{"role": "user", "content": "Reply with exactly: LOCAL LLAMA SERVER OK"}],
    "temperature": 0,
    "max_tokens": 32,
    "stream": False,
}).encode("utf-8")
req = urllib.request.Request(
    base + "/v1/chat/completions",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=300) as response:
    result = json.loads(response.read().decode("utf-8"))
text = result["choices"][0]["message"]["content"].strip()
print("response:", text)
if "LOCAL LLAMA SERVER OK" not in text:
    print("Unexpected model response", file=sys.stderr)
    raise SystemExit(2)
print("PASS")
