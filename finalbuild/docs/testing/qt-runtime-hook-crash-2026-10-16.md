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
