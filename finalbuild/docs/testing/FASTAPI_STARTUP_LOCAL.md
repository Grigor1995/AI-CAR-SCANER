# Local FastAPI startup — AI-CAR-SCANER Desktop

These checks are **real FastAPI service launches**, not the mocked backend
in packaged desktop GUI tests. Run locally, no CI/CD, no external database.

## Checkout safely

From `finalbuild/` in Git Bash:

```bash
git status --short
git switch feature/neon-ui-desktop-android-ios
git pull --ff-only origin feature/neon-ui-desktop-android-ios
```

Do not switch/pull with unrelated uncommitted local modifications.

## 1. Source startup — check this FIRST

```bash
python -m pytest -q tests/desktop/test_backend_autostart.py tests/desktop/test_backend_recovery.py tests/desktop/test_phase32_ports_and_timeout.py
python scripts/test_fastapi_startup.py --mode source
```

Expected: `[FASTAPI-START] source: PASS`. The test uses a randomized,
loopback-only port and checks JSON:
`{"status":"ok","service":"diagnostic-api",...}`.
It does not connect to PostgreSQL, connect an OBD device, or run an LLM.
It terminates only the API subprocess it started.

Failure evidence:

```bash
cat desktop-test-reports/fastapi-startup/source.json
tail -n 100 desktop-test-reports/fastapi-startup/source.log
```

## 2. Frozen backend_service.exe startup

Rebuild the EXE to incorporate the corrected PyInstaller dynamic imports,
then test the actual API process:

```bash
bash scripts/build_desktop_git_bash.sh
python scripts/test_fastapi_startup.py --mode frozen \
  --exe dist-release/icon-preview/backend_service.exe
```

Expected: `[FASTAPI-START] frozen: PASS`. Report:
`desktop-test-reports/fastapi-startup/frozen.json`.
Startup may take longer for PyInstaller onefile extraction. A failed boot
records `desktop-test-reports/fastapi-startup/frozen.log`; inspect it before
assuming backend logic is faulty.

The test uses its own private 127.0.0.1 port. It never kills an unrelated
backend process or releases another application's port.

## 3. Direct/manual source start (optional)

Only for debugging while you need a browser:

```bash
unset AI_CAR_BACKEND_URL
export AI_CAR_BACKEND_HOST=127.0.0.1
export AI_CAR_BACKEND_PORT=8001
export PYTHONPATH="$(pwd)/backend"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Then open `http://127.0.0.1:8001/health` and press Ctrl+C to stop.
Do not set `DATABASE_URL` to an external database for this investigation.

The Desktop launcher automatically owns its local FastAPI child, retries
an unexpected crash with bounded backoff, and periodically refreshes UI
connectivity. An external or cloud FastAPI process is never restarted by
Desktop.

## Release gate

`bash windows_test_runner.sh` now runs both source and frozen real-API
startup probes. `--source-only` checks source only; `--reuse-exe` does
not certify a freshly built service binary. Release readiness requires
fresh PASS reports. The UI screenshot tests still exercise a mocked API
and must not be described as real-service integration tests.

This feature branch is not merged to main until Windows evidence confirms
FastAPI startup, recovery, source regressions and packaged EXE.
