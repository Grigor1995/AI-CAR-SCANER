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

Python **3.13 x64** must be installed on Windows. The script creates an isolated
`build-release/venv-icon-preview`, runs targeted regression tests, generates
PNG/WEBP/ICO from the Desktop master, builds both executables, verifies the
embedded EXE icon and creates `dist-release/AICarScanner-icon-preview.zip`.
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

