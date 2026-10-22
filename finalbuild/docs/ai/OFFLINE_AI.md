# Managed offline GGUF AI

From `finalbuild/`, after closing an older Desktop/backend instance:

```bash
python -m apps.desktop.main --with-backend --local-ai
```

`--local-ai` explicitly selects the local llama.cpp provider for this launch,
including the child backend, even if `DIAGNOSTIC_LLM_PROVIDER` previously selected
`openai-compatible`. No OpenAI cloud account or API key is needed. The HTTP API
spoken by llama.cpp is OpenAI-compatible; that describes its request format,
not a requirement to use OpenAI's hosted service.

## Required files

Keep your GGUF in `finalbuild/models/`. The preferred default is
`Qwen3-8B-Q4_K_M.gguf`. When there is exactly one GGUF and no explicit model
selection, the launcher uses it without requiring a rename. With multiple
models, choose one explicitly in Git Bash:

```bash
export LOCAL_LLM_MODEL_PATH="C:/path/to/your/model.gguf"
```

A GGUF is model data, not an executable. The standalone llama.cpp runtime must
also exist. Extract the appropriate Windows CPU release **with its companion
DLLs** from [official llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases)
into `finalbuild/tools/llama.cpp/`, so this file exists:

```text
tools/llama.cpp/llama-server.exe
```

The launcher also checks the project/executable directory, `bin/`, an explicit
`LOCAL_LLM_SERVER_PATH` and PATH. The same lookup works in source and frozen
launches. Runtime binaries and GGUF weights are not committed or downloaded
at application startup. Offline operation requires preparing those files once.

## Endpoints and readiness

- Backend: `http://127.0.0.1:8001`.
- Managed local model: `http://127.0.0.1:8000`.
- For a custom `LOCAL_LLM_SERVER_URL`, its host/port control the managed server;
  a trailing `/v1` is normalized away. Managed startup requires loopback HTTP.
- The model loads asynchronously. Desktop remains usable while the provider
  becomes ready; large models may take time to load.
- Existing external OpenAI-compatible mode continues to use its own runtime.
  Without `--local-ai`, it never launches a competing llama-server.

An already-running backend retains its own provider/environment. Close and
restart that instance to apply `--local-ai`; the launcher does not terminate
unknown services merely because they occupy a port.

Inspect file discovery, the local AI server and the **actual backend provider**:

```bash
python scripts/check_offline_ai.py
```

The command prints JSON and exits zero only when the local runtime and the
backend's local provider are both available. It diagnoses a missing GGUF,
missing runtime, unavailable server or backend still using another provider.
On Windows the model process log is `%APPDATA%/AI-Car-Scanner/llama-server.log`.
For Git Bash:

```bash
tail -n 100 "$APPDATA/AI-Car-Scanner/llama-server.log"
```

## Verification boundary

Regression checks cover provider-mode override, executable/model discovery,
ambiguous model selection, custom URL/port normalization and real loopback
HTTP readiness checks. The cloud workspace has neither the user's GGUF weights
nor a llama-server binary: no actual model inference or Windows model-loading
performance is claimed by these tests. Verify that final step on the machine
holding the model.
