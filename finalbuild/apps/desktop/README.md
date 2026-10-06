# AI Auto Diagnostic Workstation — PySide6 Desktop

Native desktop client for Windows, Linux and macOS.

## Windows

Use the same Python environment already used by the project. If your environment is `%USERPROFILE%\Desktop\.venv`, it will be used automatically.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_desktop.ps1
python -m apps.desktop.main
```

The Desktop launcher automatically manages:

- `llama-server.exe` at `127.0.0.1:8000`
- FastAPI at `127.0.0.1:8001`
- PySide6 UI

No Flutter, Ollama runtime, or Python `llama_cpp` binding is required.

## Build

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_standalone.ps1
```
