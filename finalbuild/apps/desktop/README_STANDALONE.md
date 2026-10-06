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
