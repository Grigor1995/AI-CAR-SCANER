# Phase 35 — Adaptive LLM Context Handling

Phase 35 fixes live-data AI failures caused by an external llama-server running with a smaller
context window than the client expected.

## Key changes

- The provider reads the server's actual context from `/props`.
- Live diagnostic context is compacted to a budget derived from that value.
- `max_tokens` is capped for small servers.
- The default project launcher context is 8192.
- Existing external servers can still be used; the client adapts to their reported context.
- HTTP 400 context overflow errors are surfaced with an actionable message.

## Recommended server

```powershell
llama-server.exe `
  -m "C:\Users\grigorg\Desktop\AI-CAR-SCANER\finalbuild\models\Qwen3-8B-Q4_K_M.gguf" `
  -c 8192 `
  -t 8 `
  --host 127.0.0.1 `
  --port 8000
```

The application will also use 8192 by default when it owns the llama-server process.
