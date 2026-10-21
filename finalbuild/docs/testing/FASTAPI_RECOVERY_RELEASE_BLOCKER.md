# Desktop v1.0 — FastAPI startup / auto-recovery blocker

**Status:** CODE FIX PROPOSED ON FEATURE BRANCH — WINDOWS TESTS PENDING.

Base: the current `main` at d51c2b6, not the older diverged
`feature/neon-ui-desktop-android-ios` branch.
This fix does not change Android/iOS source, the SQLite bootstrap contract,
or GitHub Actions. Do **not** merge to main until local tests pass.

## Changes
1. The Desktop launcher preserves `--with-backend`, `--no-backend` and
   SQLite catalog initialization; exact loopback URL host/port is respected.
2. The supervisor only monitors a FastAPI process launched by Desktop, with a
   maximum of 3 restart attempts in 120 seconds and bounded backoff. Startup
   failures can also be retried. It cannot restart hosted Render/cloud APIs
   or kill an unrelated process on the same port.
3. The native GUI retries FastAPI health every 12 seconds and changes
   `Backend offline` → `Backend recovered` after a successful reconnect,
   without repeating modal errors while the API is down.
4. PyInstaller explicitly collects string-imported FastAPI and domain modules
   required by `backend_service.exe`. The Windows frozen build is **not**
   certified until it is rebuilt and the real service probe passes.
5. A real startup probe launches `apps.desktop.backend_worker` / bundled
   `backend_service.exe` using a random loopback port and an isolated
   temporary SQLite database. It verifies `/health` JSON. No external
   database, real OBD hardware, or cloud service is contacted.
6. `windows_test_runner.sh` and `desktop_v1_readiness.py` require both the
   existing tests and fresh real FastAPI boot evidence; earlier mocked GUI
   smoke tests are not interpreted as real backend proof.

## Git Bash — Windows 11 / existing Python 3.14 .venv

```bash
cd ~/Desktop/AI-CAR-SCANER/git/finalbuild
git status --short
git fetch origin
git switch --track origin/fix/desktop-v1-fastapi-recovery-20261021
# Existing local branch: git switch fix/desktop-v1-fastapi-recovery-20261021
python -m pytest -q tests/desktop/test_backend_recovery.py \
  tests/desktop/test_backend_autostart.py \
  tests/desktop/test_phase32_ports_and_timeout.py \
  apps/desktop/tests/test_main_lifecycle.py \
  apps/desktop/tests/test_ui_pom.py -k 'backend or health or recovery or startup'
python scripts/test_fastapi_startup.py --mode source
```

For source-only regression/coverage:

```bash
bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90 --core-coverage-90
```

For frozen FastAPI, first rebuild **both executables**:

```bash
bash scripts/build_desktop_git_bash.sh
python scripts/test_fastapi_startup.py --mode frozen --exe dist-release/icon-preview/backend_service.exe
```

For full release evidence (requires visible, unlocked Windows desktop):

```bash
bash windows_test_runner.sh
```

If source or frozen startup fails, inspect:

```bash
cat desktop-test-reports/fastapi-startup/source.json
tail -n 100 desktop-test-reports/fastapi-startup/source.log
cat desktop-test-reports/fastapi-startup/frozen.json
tail -n 100 desktop-test-reports/fastapi-startup/frozen.log
```

## Recovery acceptance test (manual)
- Start a **disposable local** Desktop backend (`--with-backend`).
- Verify online status, then terminate only the Desktop-owned API subprocess
  (not another application's process).
- Observe automatic recovery within the bounded attempt window.
- Confirm `Backend recovered`; verify diagnostics can be queried again.
- Repeat abnormal exits to validate max 3 attempts / 120 s.
- Close Desktop and verify no further restart occurs.
- Confirm external Render mode and `--no-backend` do not spawn processes.

## Not yet validated
- Actual Windows 11/PyInstaller backend_service.exe startup.
- End-to-end persistence after *mid-request* crash.
- Android/iOS app runtime screenshots/builds.
- Feature branch merge conflict resolution and new generated portrait
  fidelity against the user's reference mockup.
- Real vehicle/OBD adapter and hosted cloud-recovery behavior.

Any of the above must remain **PENDING** until supported by fresh reports.
