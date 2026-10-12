# AI Auto Diagnostic — Clean Windows Setup

This guide describes the native PySide6 desktop runtime and local AI services.

## 1. Model

Place the model at:

models/Qwen3-8B-Q4_K_M.gguf

## 2. Python environment

The scripts use an existing project .venv when present and otherwise fall back to .venv-desktop.

For an existing environment:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

## 3. llama.cpp server

Make sure llama-server.exe is on PATH, or set:

~~~powershell
$env:LOCAL_LLM_SERVER_PATH="C:\path\to\llama-server.exe"
~~~

Default local LLM endpoint: http://127.0.0.1:8000.

## 4. Start the application

From the finalbuild/ directory:

~~~powershell
python -m apps.desktop.main
~~~

The launcher starts or reuses llama-server on port 8000, starts FastAPI on port 8001, then opens the PySide6 workstation.

## 5. Verify services

~~~powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/v1/models
Invoke-WebRequest http://127.0.0.1:8001/health
~~~

## 6. Test local AI directly

~~~powershell
python scripts/test_local_ai.py
~~~

## 7. Test the application

Create a session, start the simulator, wait for telemetry, then press AI Analyze Live Data.

The AI context includes vehicle details, symptoms, DTCs, provenance-tagged evidence, hypotheses, telemetry summaries, recent live signal windows, and anomaly/event data. The LLM must not be treated as the deterministic diagnostic authority.
