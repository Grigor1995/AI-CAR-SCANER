from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlsplit

SOURCE_ROOT = Path(__file__).resolve().parents[2]
if getattr(sys, "frozen", False):
    BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    ROOT = Path(sys.executable).resolve().parent
else:
    BUNDLE_ROOT = SOURCE_ROOT
    ROOT = SOURCE_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HOST = os.environ.get("AI_CAR_BACKEND_HOST", "127.0.0.1")
_configured_backend_url = os.environ.get("AI_CAR_BACKEND_URL", "").rstrip("/")
_configured_backend_port = os.environ.get("AI_CAR_BACKEND_PORT", "8001")
_parsed_backend_url = urlsplit(_configured_backend_url) if _configured_backend_url else None
LOCAL_BACKEND = bool(
    _parsed_backend_url is None or (
        _parsed_backend_url.scheme == "http"
        and _parsed_backend_url.hostname in {"127.0.0.1", "localhost"}
    )
)
# Local URL port is authoritative. Otherwise Desktop could launch FastAPI on
# :8001 while its API client waits forever for http://localhost:8123/health.
PORT = int(
    _parsed_backend_url.port
    if LOCAL_BACKEND and _parsed_backend_url is not None and _parsed_backend_url.port
    else _configured_backend_port
)
BACKEND_URL = _configured_backend_url or f"http://127.0.0.1:{PORT}"
LLM_HOST = os.environ.get("LOCAL_LLM_SERVER_HOST", "127.0.0.1")
LLM_PORT = int(os.environ.get("LOCAL_LLM_SERVER_PORT", "8000"))
LLM_BASE_URL = os.environ.get("LOCAL_LLM_SERVER_URL", f"http://{LLM_HOST}:{LLM_PORT}").rstrip("/")
LLM_MODEL = os.environ.get("LOCAL_LLM_SERVER_MODEL", "Qwen3-8B-Q4_K_M.gguf")
HEALTH_URL = f"{BACKEND_URL}/health"
LLM_HEALTH_URL = f"{LLM_BASE_URL}/health"
_STARTUP_TIMEOUT = float(os.environ.get("AI_CAR_BACKEND_STARTUP_TIMEOUT", "60"))
_LLM_STARTUP_TIMEOUT = float(os.environ.get("LOCAL_LLM_SERVER_STARTUP_TIMEOUT_S", "180"))

_backend_process: subprocess.Popen[bytes] | None = None
_llm_process: subprocess.Popen[bytes] | None = None
_backend_log = None
_llm_log = None

def _close_backend_log() -> None:
    global _backend_log
    if _backend_log is not None:
        _backend_log.close()
        _backend_log = None


def _close_llm_log() -> None:
    global _llm_log
    if _llm_log is not None:
        _llm_log.close()
        _llm_log = None


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def _json_health(url: str, timeout: float = 1.0) -> bool:
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


def _backend_healthy() -> bool:
    return _json_health(HEALTH_URL)


def _llm_healthy() -> bool:
    return _json_health(LLM_HEALTH_URL)


def _appdata_log(name: str) -> Path:
    appdata = Path(os.environ.get("APPDATA", Path.home()))
    log_dir = appdata / "AI-Car-Scanner"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / name


def _resolve_llama_server() -> Path | None:
    configured = os.environ.get("LOCAL_LLM_SERVER_PATH")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())
    if getattr(sys, "frozen", False):
        candidates.extend([
            ROOT / "llama-server.exe",
            BUNDLE_ROOT / "llama-server.exe",
        ])
    which = shutil.which("llama-server.exe") or shutil.which("llama-server")
    if which:
        candidates.append(Path(which))
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            continue
    return None


def _resolve_model_path() -> Path:
    configured = os.environ.get("LOCAL_LLM_MODEL_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return (ROOT / "models" / LLM_MODEL).resolve()


def start_llama_server(wait_for_ready: bool = True) -> subprocess.Popen[bytes] | None:
    """Start llama-server; optionally return immediately while the model loads."""
    global _llm_process, _llm_log

    if os.environ.get("AI_CAR_DISABLE_LLM_AUTOSTART", "0").lower() in {"1", "true", "yes"}:
        return None
    if _llm_healthy():
        return None

    model = _resolve_model_path()
    if not model.is_file():
        print(f"[AI-Car-Scanner] Local LLM model not found: {model}", file=sys.stderr)
        return None

    server = _resolve_llama_server()
    if server is None:
        print("[AI-Car-Scanner] llama-server.exe not found; continuing with deterministic AI fallback.", file=sys.stderr)
        return None

    if _is_port_open(LLM_HOST, LLM_PORT):
        print(
            f"[AI-Car-Scanner] LLM port {LLM_PORT} is busy but {LLM_HEALTH_URL} is not healthy; "
            "local LLM autostart skipped.",
            file=sys.stderr,
        )
        return None

    log_path = _appdata_log("llama-server.log")
    _llm_log = log_path.open("ab")
    env = os.environ.copy()
    env["LOCAL_LLM_SERVER_URL"] = LLM_BASE_URL
    env["LOCAL_LLM_SERVER_MODEL"] = LLM_MODEL

    context = max(2048, int(os.environ.get("LOCAL_LLM_SERVER_CONTEXT", "8192")))
    threads = max(1, int(os.environ.get("LOCAL_LLM_SERVER_THREADS", "8")))
    command = [
        str(server),
        "-m", str(model),
        "-c", str(context),
        "-t", str(threads),
        "--host", LLM_HOST,
        "--port", str(LLM_PORT),
    ]
    if os.environ.get("LOCAL_LLM_SERVER_NO_WEBUI", "0").lower() in {"1", "true", "yes"}:
        command.append("--no-webui")

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        _llm_process = subprocess.Popen(
            command,
            cwd=str(ROOT),
            env=env,
            stdout=_llm_log,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    except OSError as exc:
        _llm_log.close()
        _llm_log = None
        print(f"[AI-Car-Scanner] Could not start llama-server.exe: {exc}", file=sys.stderr)
        return None

    if not wait_for_ready:
        # Model loading can take minutes; keep the desktop UI responsive while it loads.
        return _llm_process

    deadline = time.monotonic() + _LLM_STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if _llm_process.poll() is not None:
            returncode = _llm_process.returncode
            _llm_process = None
            _close_llm_log()
            print(
                f"[AI-Car-Scanner] llama-server exited with code {returncode}. Log: {log_path}",
                file=sys.stderr,
            )
            return None
        if _llm_healthy():
            return _llm_process
        time.sleep(0.25)

    print(
        f"[AI-Car-Scanner] llama-server did not become healthy within {_LLM_STARTUP_TIMEOUT:g}s. Log: {log_path}",
        file=sys.stderr,
    )
    process = _llm_process
    try:
        if process is not None:
            process.terminate()
            process.wait(timeout=2)
    except Exception:
        try:
            if process is not None:
                process.kill()
                process.wait(timeout=2)
        except Exception:
            pass
    _llm_process = None
    _close_llm_log()
    return None


def stop_llama_server() -> None:
    global _llm_process, _llm_log
    process = _llm_process
    _llm_process = None
    if process is not None and process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
    if _llm_log is not None:
        _llm_log.close()
        _llm_log = None


def _log_path() -> Path:
    """Backward-compatible backend log path helper used by tests/tools."""
    return _appdata_log("backend.log")


def _backend_log_path() -> Path:
    return _log_path()


def start_backend() -> subprocess.Popen[bytes] | None:
    global _backend_process, _backend_log
    # A previous child may have crashed after a successful startup.
    if _backend_process is not None and _backend_process.poll() is not None:
        _backend_process = None
        _close_backend_log()
    if not LOCAL_BACKEND:
        # The default is the shared cloud API. Do not spawn an unused local API
        # process when Desktop is configured for Render or another remote host.
        return None
    if _backend_healthy():
        return None
    if _is_port_open(HOST, PORT):
        raise RuntimeError(
            f"Port {PORT} is already in use, but {HEALTH_URL} is not healthy. "
            "Stop the process using this port or set AI_CAR_BACKEND_PORT to another port."
        )

    backend_log_path = _backend_log_path()
    _backend_log = backend_log_path.open("ab")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.pop("AI_CAR_DESKTOP_LOCAL_DB", None)
    force_local = env.get("AI_CAR_USE_LOCAL_DATABASE", "").lower() in {"1", "true", "yes"}
    if force_local or not env.get("DATABASE_URL", "").strip():
        database_file = backend_log_path.parent / "diagnostic.sqlite"
        env["DATABASE_URL"] = "sqlite:///" + database_file.resolve().as_posix()
        env["AI_CAR_DESKTOP_LOCAL_DB"] = "1"
    _backend_log.write((
        f"\n[launcher] {datetime.now(timezone.utc).isoformat()} root={ROOT}; "
        f"python={sys.executable}; storage="
        f"{'local SQLite' if env.get('AI_CAR_DESKTOP_LOCAL_DB') == '1' else 'configured DATABASE_URL'}\n"
    ).encode("utf-8"))
    _backend_log.flush()
    storage_hint = (
        " Check configured DATABASE_URL and start its database service; "
        "or explicitly select Desktop SQLite with AI_CAR_USE_LOCAL_DATABASE=1."
        if env.get("AI_CAR_DESKTOP_LOCAL_DB") != "1" else
        " Check local SQLite permissions and the active Python dependencies."
    )
    backend_path = BUNDLE_ROOT / "backend" if getattr(sys, "frozen", False) else ROOT / "backend"
    if backend_path.exists():
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(backend_path) if not existing else str(backend_path) + os.pathsep + existing
    # Keep the child bind address/port in sync with the URL Desktop is polling.
    env["AI_CAR_BACKEND_HOST"] = HOST
    env["AI_CAR_BACKEND_PORT"] = str(PORT)
    env.setdefault("DIAGNOSTIC_LLM_PROVIDER", "llama-server")
    env.setdefault("LOCAL_LLM_SERVER_URL", LLM_BASE_URL)
    env.setdefault("LOCAL_LLM_SERVER_MODEL", LLM_MODEL)

    if getattr(sys, "frozen", False):
        backend_exe = ROOT / "backend_service.exe"
        if not backend_exe.exists():
            backend_exe = BUNDLE_ROOT / "backend_service.exe"
        if not backend_exe.exists():
            _backend_log.close(); _backend_log = None
            raise RuntimeError("Bundled backend_service.exe was not found next to AICarScanner.exe.")
        command = [str(backend_exe)]
    else:
        command = [sys.executable, "-m", "apps.desktop.backend_worker"]
        env["AI_CAR_BACKEND_HOST"] = HOST
        env["AI_CAR_BACKEND_PORT"] = str(PORT)

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        _backend_process = subprocess.Popen(
            command,
            cwd=str(ROOT),
            env=env,
            stdout=_backend_log,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    except FileNotFoundError as exc:
        _backend_log.close(); _backend_log = None
        raise RuntimeError(
            "Could not start backend: uvicorn is not installed in the active Python environment."
        ) from exc
    except OSError as exc:
        _backend_log.close(); _backend_log = None
        raise RuntimeError(f"Could not start backend process: {exc}") from exc

    deadline = time.monotonic() + _STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if _backend_process.poll() is not None:
            returncode = _backend_process.returncode
            _backend_process = None
            _close_backend_log()
            raise RuntimeError(
                f"Backend exited during startup with code {returncode}. Log: {backend_log_path}{storage_hint}"
            )
        if _backend_healthy():
            return _backend_process
        time.sleep(0.25)

    process = _backend_process
    try:
        if process is not None:
            process.terminate()
            process.wait(timeout=2)
    except Exception:
        try:
            if process is not None:
                process.kill()
                process.wait(timeout=2)
        except Exception:
            pass
    _backend_process = None
    _close_backend_log()
    raise RuntimeError(f"Backend did not become healthy within {_STARTUP_TIMEOUT:g}s. Log: {backend_log_path}{storage_hint}")


def stop_backend() -> None:
    global _backend_process, _backend_log
    process = _backend_process
    _backend_process = None
    try:
        if process is not None and process.poll() is None:
            if sys.platform == "win32":
                try:
                    # Stop descendants too: a Windows child can retain the
                    # inherited log handle after its parent has exited.
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True, check=True, timeout=5,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    process.wait(timeout=5)
                    return
                except (OSError, subprocess.SubprocessError):
                    pass
            try:
                process.terminate(); process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=2)
    finally:
        _close_backend_log()


def run(argv: list[str] | None = None) -> None:
    global BACKEND_URL, HEALTH_URL, LOCAL_BACKEND
    parser = argparse.ArgumentParser(description="AI Car Scanner Desktop")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--with-backend", action="store_true", help="Start a local backend with persistent SQLite storage before opening Desktop")
    mode.add_argument("--no-backend", action="store_true", help="Connect to an existing backend without starting local services")
    args = parser.parse_args(argv or [])
    if args.with_backend:
        BACKEND_URL = f"http://127.0.0.1:{PORT}"
        HEALTH_URL = f"{BACKEND_URL}/health"
        LOCAL_BACKEND = True
        os.environ["AI_CAR_BACKEND_URL"] = BACKEND_URL
        os.environ["AI_CAR_USE_LOCAL_DATABASE"] = "1"
    try:
        from .ui import run as run_ui
    except ImportError:
        from apps.desktop.ui import run as run_ui

    backend_error: str | None = None
    backend_recovery = None
    if LOCAL_BACKEND and not args.no_backend:
        try:
            start_llama_server(wait_for_ready=False)
        except Exception as exc:
            print(f"[AI-Car-Scanner] Local LLM startup failed: {exc}", file=sys.stderr)

    if not args.no_backend:
        try:
            start_backend()
        except Exception as exc:
            backend_error = str(exc)
            print(f"[AI-Car-Scanner] Backend startup failed: {backend_error}", file=sys.stderr)

    # Only supervise the FastAPI child created by this launcher. Remote APIs
    # and an already-running externally owned local API are not restarted.
    if LOCAL_BACKEND and os.environ.get("AI_CAR_BACKEND_AUTO_RECOVER", "1").lower() in {"1", "true", "yes"}:
        try:
            from .backend_recovery import BackendRecoverySupervisor
        except ImportError:
            from apps.desktop.backend_recovery import BackendRecoverySupervisor
        backend_recovery = BackendRecoverySupervisor(
            process=lambda: _backend_process,
            restart=start_backend,
            healthy=_backend_healthy,
            # An initial import/missing-module failure may clear the child
            # before the GUI appears. Retry it without blocking Qt startup.
            allow_initial_retry=backend_error is not None,
        )
        backend_recovery.start()

    def trace_shutdown(stage: str) -> None:
        path = os.environ.get("AI_CAR_SHUTDOWN_TRACE_PATH")
        if path:
            try:
                with open(path, "a", encoding="utf-8") as stream:
                    stream.write("main: " + stage + "\n")
            except OSError:
                pass

    try:
        trace_shutdown("entering ui.run")
        run_ui()
        trace_shutdown("ui.run returned")
    finally:
        trace_shutdown("starting backend/LLM cleanup")
        if backend_recovery is not None:
            backend_recovery.stop()
        stop_backend()
        stop_llama_server()
        trace_shutdown("backend/LLM cleanup complete")

    if backend_error and not _backend_healthy():
        # A recovered initial failure is not an EXE shutdown failure.
        raise SystemExit(1)


if __name__ == "__main__":
    run(sys.argv[1:])
