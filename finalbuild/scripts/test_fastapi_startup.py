#!/usr/bin/env python3
"""Launch actual source/frozen FastAPI locally, verify /health and record evidence.

This is NOT the mock backend used by visible UI smoke tests.
No CI/CD, remote database, network calls or physical vehicle are required.
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
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desktop-test-reports" / "fastapi-startup"


def ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def is_healthy(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/health", timeout=1.0) as response:
            data = json.load(response)
            return (
                response.status == 200 and isinstance(data, dict)
                and data.get("status") == "ok"
                and data.get("service") == "diagnostic-api"
            )
    except (OSError, ValueError, TypeError):
        return False


def stop_child(process: subprocess.Popen, frozen: bool) -> None:
    if process.poll() is not None:
        return
    if frozen and sys.platform == "win32":
        # Only terminate the exact PyInstaller process and its child tree.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, check=False, timeout=20,
        )
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def run_probe(mode: str, exe: Path | None, timeout: float) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / f"{mode}.log"
    json_path = OUT / f"{mode}.json"
    port = ephemeral_port()
    started = time.monotonic()
    status = "FAIL"
    exit_code = None
    error = None

    with tempfile.TemporaryDirectory(prefix="aicar-fastapi-") as temp:
        env = os.environ.copy()
        env["APPDATA"] = temp
        env["DATABASE_URL"] = "sqlite:///" + (Path(temp) / "diagnostic.sqlite").as_posix()
        env["AI_CAR_DESKTOP_LOCAL_DB"] = "1"
        env["AI_CAR_BACKEND_HOST"] = "127.0.0.1"
        env["AI_CAR_BACKEND_PORT"] = str(port)
        env["AI_CAR_DISABLE_LLM_AUTOSTART"] = "1"
        env["NO_PROXY"] = "127.0.0.1,localhost"
        env["no_proxy"] = env["NO_PROXY"]
        env.pop("AI_CAR_BACKEND_URL", None)
        if mode == "source":
            env["PYTHONPATH"] = (
                str(ROOT) + os.pathsep + str(ROOT / "backend")
                + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
            )
            command = [sys.executable, "-m", "apps.desktop.backend_worker"]
        else:
            if exe is None or not exe.is_file():
                error = f"Frozen backend EXE missing: {exe}"
                command = None
            else:
                env.pop("PYTHONPATH", None)
                command = [str(exe)]

        if command is not None:
            with log_path.open("wb") as logfile:
                proc = subprocess.Popen(
                    command, cwd=str(ROOT), env=env,
                    stdout=logfile, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    if sys.platform == "win32" else 0,
                )
                try:
                    while time.monotonic() - started < timeout:
                        exit_code = proc.poll()
                        if exit_code is not None:
                            break
                        if is_healthy(port):
                            status = "PASS"
                            break
                        time.sleep(0.4)
                except Exception as exc:
                    error = str(exc)
                finally:
                    stop_child(proc, frozen=(mode == "frozen"))
        else:
            log_path.write_text(str(error), encoding="utf-8")

    result = {
        "status": status, "mode": mode, "health": status == "PASS",
        "port": port, "elapsed_seconds": round(time.monotonic() - started, 2),
        "exit_code_before_cleanup": exit_code,
        "error": error, "log": str(log_path.relative_to(ROOT)),
    }
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[FASTAPI] {mode}: {status} | {json_path}", flush=True)
    if status != "PASS":
        print("\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-65:]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("source", "frozen", "both"), default="source")
    parser.add_argument("--exe", default="dist-release/icon-preview/backend_service.exe")
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()
    if not 5 <= args.timeout <= 300:
        parser.error("--timeout must be 5..300 seconds")
    if args.mode in {"frozen", "both"} and sys.platform != "win32":
        parser.error("Frozen startup probe requires Windows")
    exe = (ROOT / args.exe).resolve()
    modes = ["source", "frozen"] if args.mode == "both" else [args.mode]
    results = [run_probe(mode, exe, args.timeout) for mode in modes]
    return 0 if all(result["status"] == "PASS" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
