# Frozen Windows Desktop startup crash — 2026-10-16

## Confirmed user-local observations

- **Source-mode UI works:** `python apps/desktop/main.py` on the existing Python 3.14.7 venv.
- **Onefile GUI crashes:** `dist-release/icon-preview/AICarScanner.exe` exits with `Segmentation fault`.
- **Onedir console GUI also crashes:** `dist-debug/AICarScannerDebug/AICarScannerDebug.exe` exits with status **139**, with custom native taskbar icon code disabled.
- The PyInstaller bootloader loads `python314.dll` and enters embedded Python.
- It executes `debug_runtime_hook.py`, `pyi_rth_cryptography_openssl.py`, and reaches **`pyi_rth_pyside6.py`**.
- `faulthandler` reports **Windows access violation during `create_embedded_qt_conf`**, in a native import under `importlib`.
- **No application `main.py` frames are present in this crash.** The crash occurs before the Desktop application entrypoint.
- `qt-probe.log` and its exit status were not provided in the pasted output, so the Qt probe cannot yet be declared PASS or FAIL.

## Diagnosis and scope

The fatal failure is at the **PyInstaller/PySide6 runtime initialization boundary**. There is not enough evidence to name the underlying DLL, Qt/Shiboken version conflict, incompatible native package, or PATH collision. A fatal native crash cannot be caught with a Python try/except.

The custom ctypes-based Windows taskbar icon code cannot be the immediate failing call in the provided trace because the interpreter has not reached application startup and that code was explicitly bypassed. Avoid rewriting functional UI and AI logic to address this traceback.

Qt for Python packaging documentation warns that a system-level PySide6/shiboken6 installation can interfere with the active virtual environment's chosen libraries. Confirm paths and hashes before changing installed packages.

## Zero-rebuild triage (Git Bash, from finalbuild/)

```bash
git status --short
git pull --ff-only origin main
grep -E '\[DIAG\] Qt probe exit status' desktop-debug-build.log
grep -E '\[QT-PROBE\]|Fatal|access violation|Error' dist-debug/qt-probe.log | tail -n 40
python scripts/diagnose_frozen_qt.py
python -m pip check
```

If `python` does not resolve to the intended Python 3.14 venv, use its explicit
`Scripts/python.exe`. The package-audit script uses only the Python standard
library; it does not load PySide6 DLLs, install packages, or re-run the build.

Its output `dist-debug/qt-bundle-audit.json` compares hashes and file
locations of PySide6/Qt6/Shiboken/OpenSSL/native runtime libraries between
the minimal Qt probe bundle and the actual frozen Desktop bundle.

## Branching next tests

- **Qt probe also crashes in pyi_rth_pyside6:** investigate the shared PySide6/Shiboken/PyInstaller/native Python DLL set and environment, and test a small frozen Qt app before app changes.
- **Qt probe passes but real Desktop crashes:** compare DLL checksums/locations, version matrix, and paths; the difference in collected dependencies is a high-priority hypothesis. Optionally freeze the minimal Qt probe with Desktop-only hidden imports to localize the contaminating dependency.
- **DLLs differ by hash or duplicate basename:** inspect collection origin; do not blindly delete binary files from bundles before understanding dependencies.
- **DLLs match but the Desktop crashes:** do not assume packages are sound; isolate runtime hooks and hidden dependencies by controlled minimal builds.
- **Runtime hook succeeds but later code crashes:** only then examine Desktop-specific startup, application icons, or API/backend lifecycle.

## Current status

**FAIL — frozen Windows runtime startup**; build output existing, application not usable as an EXE. No pass status or release approval claimed. The Python source UI remains working; Python 3.14 virtual environment is preserved. All debug files go to `dist-debug/`, and the existing release artifacts remain untouched.

## Update after real Qt probe and bundle audit (2026-10-16)

User-local results:

- **AIQtProbe.exe: exit 0.** QtCore/QtGui/QtWidgets, QApplication, application icon and the minimal event loop all worked.
- **AICarScannerDebug.exe: exit 139**, in `pyi_rth_pyside6.py` before the application entrypoint, even with native taskbar icon fallback disabled.
- Both bundles contain 29 matching native DLL/PYD files included by the selected Qt/SSL audit filter; **no hash differences** in that subset. This does not establish that all collected native binaries are identical.
- `pip check`: **No broken requirements found.**
- Versions: Windows Python 3.14.7, PySide6 / PySide6_Essentials / PySide6_Addons / shiboken6 6.11.2, PyInstaller 6.22.3, pyinstaller-hooks-contrib 2026.8.

PyInstaller 6.22.3 `pyi_rth_pyside6.py` calls `create_embedded_qt_conf("PySide6", ...)`, which imports QtCore on the reported stack. The actual Desktop bundle also executes `pyi_rth_cryptography_openssl.py` before the Qt runtime hook. This suggests a **testable DLL/import-order interaction**, not a proven cryptography bug.

Two optional isolation tests are now available. Both preserve the source UI, the existing Python venv and prior release outputs:

**Experiment A — early QtCore module import before other PyInstaller runtime hooks**

```bash
git pull --ff-only origin main
bash scripts/debug_desktop_git_bash.sh --desktop-only 2>&1 | tee desktop-debug-build.log
bash scripts/run_debug_desktop_git_bash.sh --early-qtcore
```

The first command rebuilds only the diagnostic Desktop EXE using the already passing minimal Qt probe as a baseline. The second toggles `AI_CAR_EARLY_QTCORE=1` to import `PySide6.QtCore` in the diagnostic hook before subsequent built-in hooks. This is an **experiment**, not production startup code. Success would narrow the problem to runtime initialization order. Failure still leaves the application source code unimplicated.

**Experiment B — reproduce Desktop's extra cryptography runtime hook in minimal Qt probe**

```bash
bash scripts/probe_qt_crypto_git_bash.sh 2>&1 | tee qt-crypto-build.log
```

Outputs: `dist-debug/qt-crypto-probe.log` and `dist-debug/crypto-probe-faults.log`. The isolated Qt probe is frozen with `--hidden-import cryptography.hazmat.bindings._rust` to collect cryptography's PyInstaller hook and native dependencies. Compare `Crypto Qt probe exit status` with the original `AIQtProbe` exit 0.

If experiment B passes, the failure requires some other Desktop-specific dependency or native initialization difference. If it fails at the same runtime hook, narrow the cryptography/OpenSSL load-order hypothesis with a controlled runtime-hook exclusion and compare dependency graph before changing release builds.

**Release gate remains FAIL until the normal executable opens and passes a diagnostic workflow.**

## Update: frozen GUI now launches with early QtCore; separate shutdown regression (October 16)

User's new onedir diagnostic run with `--early-qtcore`:

- **Desktop GUI displayed successfully**, proving that the QtCore import-order
  workaround changes frozen startup from the previous Windows access violation.
- Upon closing the GUI, **exit status 127** (as reported by the runner), with
  the Qt diagnostic message **`QThread: Destroyed while thread '' is still running`**.
  The user's prose also calls this exit 139, but the pasted new run reports 127;
  previous frozen runs did report 139. Do not conflate these exit statuses.
- Startup and shutdown must be treated as **two independent regressions**.
  Native taskbar icon fallback remained disabled in the working-startup run.

### Applied code changes; Windows verification still required

1. `apps/desktop/qt_early_runtime_hook.py` is now registered in the canonical
   `apps/desktop/specs/AICarScanner.spec` and the onedir debug builder so
   QtCore initializes before PyInstaller's later runtime hooks **without a
   command-line opt-in**. This is a narrow Windows frozen-startup workaround,
   not a claim that the original third-party native conflict is explained.
2. `apps/desktop/ui.py` now tracks and owns its `Worker(QThread)` instances.
   A window close with active jobs is **deferred**; it stops polling timers,
   requests interruption, and waits asynchronously for worker-completion
   signals without blocking the GUI event loop. It does **not** forcibly kill
   an active HTTP request, which may run until its configured timeout.
3. Only after `QThread.finished`, on the GUI thread, the slot joins the
   already-completed native thread (`wait()`), removes the strong reference,
   and schedules deletion. After the last worker exits, it retries window close.
4. Late worker completions/errors are not allowed to update a closing GUI
   or open modal error dialogs.
5. Frozen Windows defaults to Qt-managed QIcon/window/executable artwork
   (which already loads correctly); the unverified low-level Win32 ctypes
   fallback can be re-enabled explicitly with
   `AI_CAR_DISABLE_NATIVE_TASKBAR_ICON=0` in a controlled test.
6. Added unit/regression tests for shutdown deferral and new-job blocking,
   plus a static packaging test for the QtCore runtime hook.

### Verify on the user's Windows computer, from finalbuild/ Git Bash

```bash
git status --short
git pull --ff-only origin main
python -m pytest -q tests/desktop/test_phase25_standalone.py \
  apps/desktop/tests/test_main_helpers.py
bash scripts/debug_desktop_git_bash.sh --desktop-only 2>&1 | tee desktop-debug-build.log
bash scripts/run_debug_desktop_git_bash.sh
```

If the window opens, let backend health/device requests finish, then close it.
Check `GUI exit status` for `0`. If the Qt worker error persists, inspect
`dist-debug/desktop-run.log` and the new `python-faults.log` segment.

Then (only after a clean debug exit) generate a fresh release EXE:

```bash
bash scripts/build_desktop_git_bash.sh 2>&1 | tee desktop-build.log
export AI_CAR_BACKEND_URL=https://ai-car-scaner.onrender.com
export AI_CAR_DISABLE_LLM_AUTOSTART=1
./dist-release/icon-preview/AICarScanner.exe
echo "Release exit code: $?"
```

A build check, static unit test, or a successful initial window appearance
alone does not establish a stable production release. A source-compatible fix
has been committed, but actual **Windows clean shutdown remains unverified**.


## Update: Qt runs, but packaged GUI still exits abnormally on close

The user's latest successful-launch log shows `LOADER: OK`, `manually flushing
stdout and stderr`, `cleaning up Python interpreter`, `unloading Python
shared library`, `end of process reached`, then Qt library unload messages
for `qmodernwindowsstyle.dll` and `qwindows.dll`. The user reports **exit
139 on window close**. The latest pasted tail does **not** show the prior
`QThread: Destroyed while thread ... is still running` diagnostic.

**Do not assign root cause to the unloaded DLLs based on the tail alone:**
Qt plugins can unload during a normal application shutdown, and the native
crash could instead occur during unrelated teardown. Exit 139 remains FAIL.

The code now supports an **opt-in teardown experiment**, enabled only by
`AI_CAR_QT_EXPLICIT_CLEANUP=1` in a frozen Windows process: after
`QApplication.exec()` returns, `MainWindow` is scheduled for deletion,
pending `DeferredDelete` events are delivered and the GUI event queue is
processed before control returns to the Desktop entrypoint. This is
experimental and is **off by default**, including in production builds.

Lifecycle checkpoints (closeEvent, QThread.finished, QApplication.exec
exit, optional explicit cleanup, return to main, and backend/LLM cleanup)
are emitted **only when** `AI_CAR_SHUTDOWN_TRACE_PATH` is set.

Run from `finalbuild/` in Windows Git Bash:

```bash
git status --short
git pull --ff-only origin main
python -m pytest -q apps/desktop/test_smoke.py
QT_QPA_PLATFORM=offscreen python -m pytest -q \
  apps/desktop/tests/test_ui_pom.py \
  -k "shutdown_trace_is_opt_in or close_waits_for_active_api_workers or run_worker_rejects_new_background_jobs"
bash scripts/debug_desktop_git_bash.sh --desktop-only 2>&1 | tee desktop-debug-build.log

# A: baseline
bash scripts/run_debug_desktop_git_bash.sh

# B: Windows style-plugin isolation; Fusion avoids the native Windows style
bash scripts/run_debug_desktop_git_bash.sh --fusion

# C: opt-in Qt object cleanup; no native DLLs are manually unloaded
bash scripts/run_debug_desktop_git_bash.sh --explicit-cleanup

# Optional D: combine Fusion style with explicit cleanup
bash scripts/run_debug_desktop_git_bash.sh --fusion --explicit-cleanup
```

For each run, **open the GUI, allow any initial API requests to finish,
then close normally**. The script prints the actual exit code and writes
independent logs under `dist-debug/`, including
`shutdown-trace-baseline.log`,
`shutdown-trace-baseline-fusion.log`, and
`shutdown-trace-baseline-cleanup.log` as well as matching
`desktop-run-*.log` and `python-faults-*.log` files. Baseline still uses
`dist-debug/desktop-run.log` for compatibility.

### Decision table

- **Baseline 139, Fusion 0:** investigate the Windows native Qt style plugin
  or style-related destruction path before considering `Fusion` as default.
- **Baseline 139, cleanup 0:** confirm deterministic Qt object destruction
  as a stable frozen shutdown strategy, then promote it to release code with
  regression tests.
- **All variants 139, trace shows `ui: returning to main.run`:**
  inspect backend cleanup, interpreter teardown and native DLL detach using
  a real Windows dump (WER/WinDbg); the tail alone cannot locate a native fault.
- **Trace never reaches `ui: QApplication.exec returned`:** investigate
  callbacks and QThread/UI destruction still happening during event-loop exit.

No build, live Windows test, or clean process exit is claimed in this report.
