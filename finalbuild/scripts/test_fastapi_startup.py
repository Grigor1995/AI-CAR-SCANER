#!/usr/bin/env python3
"""Real FastAPI startup probe (not a mocked health endpoint).

Use from finalbuild:
  python scripts/test_fastapi_startup.py --mode source
  python scripts/test_fastapi_startup.py --mode frozen \
    --exe dist-release/icon-preview/backend_service.exe

Runs an isolated temporary local HTTP server and writes backend diagnostics.
Does not use CI/CD, PostgreSQL, external URLs, or a physical OBD adapter.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def get_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def is_our_backend(url: str) -> bool:
    try:
        with urlopen(url + "/health", timeout=2) as response:
            if response.status != 200:
                return False
            payload = json.load(response)
        return (
            isinstance(payload, dict)
            and payload.get("status") == "ok"
            and payload.get("service") == "diagnostic-api"
        )
    except (OSError, URLError, HTTPError, ValueError, TypeError):
        return False


def terminate_owned_process(
    process: subprocess.Popen, timeout: int = 10, frozen: bool = False
) -> None:
    if process.poll() is not None:
        return
    if frozen and sys.platform == "win32":
        # PyInstaller onefile bootloader owns a second child process. Kill the
        # precise launched PID and its children so no backend is left behind.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False, capture_output=True, timeout=20,
        )
        process.wait(timeout=10)
        return
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False, capture_output=True, timeout=20,
            )
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)


def probe(mode: str, exe: Path | None, timeout: float) -> dict:
    port = get_port()
    url = f"http://127.0.0.1:{port}"
    report_dir = ROOT / "desktop-test-reports" / "fastapi-startup"
    report_dir.mkdir(parents=True, exist_ok=True)
    logfile = report_dir / f"{mode}.log"
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)  # Never connect to a developer's real DB.
    env["AI_CAR_DISABLE_LLM_AUTOSTART"] = "1"
    env["AI_CAR_BACKEND_HOST"] = "127.0.0.1"
    env["AI_CAR_BACKEND_PORT"] = str(port)
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = "127.0.0.1,localhost"
    env.pop("AI_CAR_BACKEND_URL", None)
    if mode == "source":
        root = str(ROOT / "backend")
        env["PYTHONPATH"] = (
            root if not env.get("PYTHONPATH")
            else root + os.pathsep + env["PYTHONPATH"]
        )
        command = [
            sys.executable, "-m", "uvicorn", "api.main:app",
            "--host", "127.0.0.1", "--port", str(port),
        ]
    else:
        if exe is None or not exe.is_file():
            raise FileNotFoundError(f"Built backend_service.exe is missing: {exe}")
        env.pop("PYTHONPATH", None)
        command = [str(exe)]

    started_at = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="ai-car-fastapi-probe-") as appdata:
        env["APPDATA"] = appdata
        with logfile.open("wb") as log:
            process = subprocess.Popen(
                command, cwd=str(ROOT), env=env,
                stdout=log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                if sys.platform == "win32" else 0,
            )
            healthy = False
            exit_code = None
            try:
                while time.monotonic() - started_at < timeout:
                    exit_code = process.poll()
                    if exit_code is not None:
                        break
                    if is_our_backend(url):
                        healthy = True
                        break
                    time.sleep(0.5)
            finally:
                # Stop ONLY the process launched by this test, not an existing API.
                terminate_owned_process(process, frozen=mode == "frozen")
    report = {
        "mode": mode,
        "status": "PASS" if healthy else "FAIL",
        "healthy": healthy,
        "port": port,
        "elapsed_seconds": round(time.monotonic() - started_at, 2),
        "returncode_before_teardown": exit_code,
        "log_file": str(logfile),
    }
    (report_dir / f"{mode}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[FASTAPI-START] {mode}: {report['status']} | port={port} | log={logfile}")
    if not healthy:
        tail = logfile.read_text(encoding="utf-8", errors="replace").splitlines()[-65:]
        print("\n".join(tail))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("source", "frozen", "both"), default="source")
    parser.add_argument(
        "--exe", default="dist-release/icon-preview/backend_service.exe",
        help="Relative path under finalbuild to frozen FastAPI EXE",
    )
    parser.add_argument("--timeout", type=float, default=75.0)
    args = parser.parse_args()
    if args.timeout < 5 or args.timeout > 300:
        parser.error("--timeout must be between 5 and 300 seconds")
    if args.mode in {"frozen", "both"} and sys.platform != "win32":
        parser.error("Frozen backend tests require Windows")
    exe = (ROOT / args.exe).resolve()
    results = [probe(mode, exe, args.timeout) for mode in
               (("source", "frozen") if args.mode == "both" else (args.mode,))]
    return 0 if all(x["status"] == "PASS" for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
