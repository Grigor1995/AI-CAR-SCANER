# Desktop — separate FastAPI, acquisition, and AI provider status

Originally developed on `fix/desktop-v1-fastapi-recovery-20261021`; integrated with the current UI/privacy changes on 2026-10-22. See [branch merge review](branch-merge-review-2026-10-22.md).
Real source startup/crash/recovery passed in Linux. Windows frozen runtime validation remains pending.

## Why the earlier UI was contradictory

- Status-bar **Backend online** = `GET /health` returned `{"status":"ok"}`.
- Live Data **Backend unavailable** was generated from **any** error from
  `GET /api/v1/acquisition/sessions/{id}/status`. A session can be valid and
  FastAPI healthy but acquisition never started. In this case FastAPI
  intentionally returns HTTP 404 **Acquisition not started**.
- AI **OFFLINE** = independent `GET /api/v1/ai/provider` status. In the
  default configuration the provider expects `llama-server.exe` and an
  available GGUF model at localhost port 8000.

The Desktop now displays **Acquisition not started**, **Session not found**,
**Acquisition unavailable**, or **Backend offline** as distinct states.
Acquisition errors are visible as a tooltip. After a backend reconnect,
the active Live Data page also updates the provider status. AI runtime
availability errors can be inspected by hovering over the AI label.

## Local provider options (all expose OpenAI-compatible endpoints)

- **LM Studio:** easiest interactive Windows setup. Developer → Start server.
  By default `http://127.0.0.1:1234`. Official docs: https://lmstudio.ai/docs/developer/core/server
- **llama.cpp llama-server:** direct low-overhead GGUF inference; already
  integrated, with configurable GGUF context, localhost port 8000.
- **Jan:** open-source Windows-friendly UI and local server; default
  `http://127.0.0.1:1337`. Official docs: https://docs.jan.ai/desktop/api-server
- **Cloud OpenAI-compatible gateway:** can use the same adapter if the
  upstream endpoint, provider auth and supported API match; do not upload
  confidential vehicle data without user consent.

Ollama, LM Studio, Jan and llama.cpp are *runtimes*, not AI model quality
levels. The model itself, context length, prompt construction, hardware,
retrieved evidence, evaluation suite and deterministic safeguards matter.

## LM Studio — FastAPI + native Desktop (Git Bash)

1. Install LM Studio from https://lmstudio.ai/download?os=windows
2. Download/load an instruction model suitable for the RAM/VRAM.
3. Developer → Start server. Keep it bound to `127.0.0.1` (not 0.0.0.0).
4. From `finalbuild/` in Git Bash, fetch the exact model ID:

```bash
curl -fsS http://127.0.0.1:1234/v1/models
```

5. In the **same** Git Bash terminal that starts the Desktop app:

```bash
export DIAGNOSTIC_LLM_PROVIDER=openai-compatible
export LLM_BASE_URL=http://127.0.0.1:1234
export LLM_MODEL='PASTE-EXACT-ID-FROM-/v1/models'
export AI_CAR_DISABLE_LLM_AUTOSTART=1
python -m apps.desktop.main --with-backend
```

Replace `LLM_MODEL` with the exact `data[0].id` (or another loaded ID).
Restart the local FastAPI process after changing these variables. Don't
use the same port for FastAPI (8001) and LM Studio (1234).

Open the API provider report after the Desktop has started:

```bash
curl -fsS http://127.0.0.1:8001/health
curl -fsS http://127.0.0.1:8001/api/v1/ai/provider
```

The provider response should list `available: true` and the intended model.
`available: true` means the server advertises the model, not that a
diagnostic answer is guaranteed. Test a real AI request and verify grounding
against P0302/LPG golden cases before release.

## Local regression tests

```bash
python -m pytest -q apps/desktop/tests/test_ui_widgets.py \
  tests/ai/test_low_coverage_openai_compatible.py \
  tests/ai/test_openai_runtime_availability.py \
  tests/ai/test_llm_factory.py
bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90
```

The `47 passed` and frozen/source API recovery checks confirmed earlier
must not be taken as evidence that these *new AI/UI changes* passed.
