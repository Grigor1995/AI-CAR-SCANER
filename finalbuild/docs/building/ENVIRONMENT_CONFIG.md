# Shared JSON environment configuration

Desktop, the backend and the local setup/launch runner share one loader in
`shared/environment.py`. Values are applied inside application processes;
Windows user/system environment variables and PATH are not permanently changed.

## Configuration files

- Shipped defaults: `finalbuild/config/environment.json`.
- Development overrides: `finalbuild/config/environment.local.json` (ignored by Git).
- Compiled Desktop overrides: `environment.local.json` beside the executable.
- Explicit configuration: set `AI_CAR_ENV_CONFIG` to any JSON file.
- Online installer: creates `<installation>/environment.json`; shortcuts pass
  its location through `AI_CAR_ENV_CONFIG` automatically.

Restart the application after editing configuration. UTF-8 is supported. Use
absolute paths for local model/server files; backslashes must be escaped in
JSON, or use forward slashes on Windows.

```json
{
  "version": 1,
  "environment": {
    "AI_CAR_BACKEND_PORT": 8001,
    "LOCAL_LLM_SERVER_PORT": 8000,
    "LOCAL_LLM_SERVER_THREADS": 8,
    "LOCAL_LLM_SERVER_CONTEXT": 8192,
    "LOCAL_LLM_MODEL_PATH": "C:/Models/my-model.gguf",
    "LOCAL_LLM_SERVER_PATH": "C:/AI/llama-server.exe",
    "AI_CAR_DISABLE_LLM_AUTOSTART": false
  }
}
```

Strings, numbers and booleans are accepted. Booleans become `1` or `0` for
existing ENV readers. Nested values, unsupported versions, malformed files and
missing explicitly selected files fail visibly instead of silently using a
different configuration. ENV names must use uppercase letters, digits and
underscores. Keep API keys and machine-specific values in local files.

## Precedence

For direct Desktop/backend launches, explicit process ENV wins over JSON;
the explicit JSON file wins over the local JSON file, then shipped defaults.
The runner additionally places its saved `.runner-state.json` tool paths/ports
between shipped defaults and local/explicit JSON. A process ENV always wins.
An explicit `LOCAL_LLM_SERVER_URL` is respected; otherwise the URL is derived
from the configured AI host and port.

`runner.py setup --port ... --ai-port ...` saves setup choices; process ENV or
local JSON may override those saved defaults at launch. Desktop and AI ports
must differ. The runner's health checks and emulator URL use effective ports.
For a remote Android backend use `AI_CAR_ANDROID_API_URL` or the existing
`runner.py android --api-url ...` option. An explicit Android command-line URL
wins. A direct Uvicorn command still owns its CLI bind address and port.

The installer preserves custom JSON settings during repair/upgrades and
updates only its chosen AI model/runtime paths and AI startup toggle. Selecting
an external GGUF does not copy it; retain that file at its configured location.
Uninstall removes the installer-owned JSON; external GGUF files and user
records in AppData remain untouched.
