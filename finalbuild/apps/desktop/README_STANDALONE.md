# Standalone Windows build

Phase 25 builds the PySide6 Desktop application and the FastAPI backend as separate PyInstaller executables.

Why separate executables?
- A frozen GUI executable should not be used as the Python interpreter for `-m uvicorn`.
- `AICarScanner.exe` starts `backend_service.exe` and owns its lifecycle.
- The two executables can be shipped together and later wrapped in a single installer.

Build on Windows:

```powershell
.\.venv-desktop\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv-desktop\Scripts\python.exe -m pip install -r apps\desktop\requirements.txt
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_standalone.ps1
```

Run:

```powershell
.\dist\AICarScanner\AICarScanner.exe
```

The GUI reuses an already healthy local backend. Otherwise it starts the bundled `backend_service.exe` automatically.

## Windows x64 build from Git Bash (recommended for local icon review)

From `finalbuild/` in **Git Bash** (not WSL):

```bash
git status --short
bash -n scripts/build_desktop_git_bash.sh
bash scripts/build_desktop_git_bash.sh
```

The Git Bash builder **reuses the existing Python 3.14 x64 virtual environment**.
It checks `apps/desktop/.venv`, `Desktop/.venv`, `finalbuild/.venv`,
the parent `.venv`, and `~/Desktop/.venv` (as well as an activated venv).
Select the exact location explicitly when needed:

```bash
export AI_CAR_DESKTOP_VENV="$HOME/Desktop/.venv"
bash scripts/build_desktop_git_bash.sh
```

There is no new virtual environment and no Python 3.13 installation.
The existing venv receives any missing backend/Desktop test/build dependencies
through `pip install -r`. The script runs targeted regression tests, generates
PNG/WEBP/ICO from the Desktop master, builds both executables, verifies the
embedded EXE icon, and creates `dist-release/AICarScanner-icon-preview.zip`.
It never deletes `dist/` or arbitrary uncommitted source files. Changes to
generated tracked icons require an explicit save/commit before regeneration.

To launch the preview using the hosted API, from `finalbuild/`:

```bash
export AI_CAR_BACKEND_URL=https://ai-car-scaner.onrender.com
export AI_CAR_DISABLE_LLM_AUTOSTART=1
./dist-release/icon-preview/AICarScanner.exe
```

A successful build or icon report does **not** establish that the GUI starts
without crashing; visually inspect the Explorer, taskbar and window icons
and manually test a complete diagnostic flow.


## Troubleshooting: packaged EXE exits with Segmentation fault

If `python apps/desktop/main.py` works but the frozen executable exits immediately,
isolate bootloader, Qt plugins, and native taskbar handling before changing UI code.
The existing release EXE is `onefile` with no console; it suppresses details that
a console/debug build can expose. **Keep using the existing Python 3.14 x64 venv.**

From `finalbuild/` in Git Bash:

```bash
git pull --ff-only origin main
bash -n scripts/debug_desktop_git_bash.sh
bash -n scripts/run_debug_desktop_git_bash.sh
bash scripts/debug_desktop_git_bash.sh 2>&1 | tee desktop-debug-build.log
```

The command creates a **minimal Qt test app** and a full Desktop app using
`--onedir --console --debug bootloader` in `dist-debug/`. It does not remove
`dist-release/`, `dist/`, or the Python venv. The minimal Qt test starts,
shows a small window, then closes automatically.

After building:

```bash
bash scripts/run_debug_desktop_git_bash.sh
```

Close the GUI normally if it opens. The script shows process status and the end
of `dist-debug/desktop-run.log` and `dist-debug/python-faults.log`. The first
run disables only the custom ctypes-based Windows taskbar icon fallback, while
still using normal Qt and EXE icons. To compare, **only if the first run works**:

```bash
bash scripts/run_debug_desktop_git_bash.sh --native-icon
```

Interpretation:
- **Qt probe crashes**: investigate Qt/PySide6 package and plugin paths first.
- **Qt probe works, Desktop debug crashes**: inspect the final Python/native
  stack and module loading; isolate Desktop import and startup code.
- **Debug Desktop works, normal onefile crashes**: investigate onefile extraction,
  windowed bootloader and DLL/runtime conditions. Prefer a stable onedir
  distribution over prematurely shipping a crashing onefile build.
- **Native-icon-disabled works; enabled crashes**: isolate the custom Win32
  icon creation path before using it in any release.

**Do not mark this regression fixed** until the target Windows executable
actually launches, runs a diagnostic session, and exits cleanly.
