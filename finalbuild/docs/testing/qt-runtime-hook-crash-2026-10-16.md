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
