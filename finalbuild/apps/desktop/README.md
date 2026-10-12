# AI CAR SCANER — Native Desktop Client

The canonical desktop workstation is implemented in **Python + PySide6**. It uses the shared FastAPI backend and the same diagnostic-session contract as the native Android and iOS clients.

## Run from the repository

From the finalbuild/ directory, activate your Python environment, install the relevant dependencies, and run:

~~~powershell
python -m pip install -r apps\desktop\requirements.txt
python -m apps.desktop.main
~~~

The launcher can use or start the configured local backend and local llama-server.exe according to the runtime settings. See [Windows setup](../../START_HERE_WINDOWS.md) for the complete local setup.

## Standalone Windows package

See [README_STANDALONE.md](README_STANDALONE.md) for the PyInstaller build and launch instructions. The desktop GUI and backend service are packaged separately.

## Tests

From finalbuild/:

~~~bash
python -m pytest -p no:benchmark -p no:asyncio apps/desktop/tests
python -m pytest -p no:benchmark -p no:asyncio apps/desktop/test_smoke.py
~~~

The Python test suite covers the API client, models, persistence, main-window helpers, and selected UI behavior. A passing unit test suite does not by itself prove that a packaged Windows executable runs correctly.

## Shared backend

The Desktop client defaults to the local FastAPI service at `http://127.0.0.1:8001` and starts it automatically when needed. Set `AI_CAR_BACKEND_URL=https://ai-car-scaner.onrender.com` to use the hosted API instead. Standard API requests use an 8-second timeout so unavailable endpoints fail promptly; live AI analysis has its own longer timeout. The backend's deterministic analysis remains authoritative; optional LLM output must preserve uncertainty and evidence provenance.
