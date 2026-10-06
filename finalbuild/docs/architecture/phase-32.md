# Phase 32 — Clean Local AI Runtime

## Services

| Service | Address |
|---|---|
| llama.cpp server | `http://127.0.0.1:8000` |
| FastAPI backend | `http://127.0.0.1:8001` |

## Desktop lifecycle

`AICarScanner` checks the llama-server health endpoint and starts `llama-server.exe` when necessary. It then starts the FastAPI backend and opens the PySide6 workstation. The Desktop owns and terminates only processes it started itself.

## AI provider

`LlamaServerLLMProvider` talks to the OpenAI-compatible `/v1/chat/completions` endpoint. It uses the model id reported by `/v1/models` when the configured filename is not the server's runtime id and exactly one model is loaded.

## Timeouts

Local CPU inference defaults to 300 seconds. Desktop live-data AI calls use a 300-second client timeout. Health checks remain short.

## Safety

The LLM is explanatory/orchestration-only and never gets ECU write/programming authority.
