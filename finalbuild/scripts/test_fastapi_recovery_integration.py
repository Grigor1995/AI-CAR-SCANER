#!/usr/bin/env python3
"""Real local FastAPI crash -> bounded auto-restart integration test.

This starts ONLY disposable child processes and a temporary SQLite database.
Does not touch the user's running API, permanent database, or OBD devices.
Run from finalbuild: python scripts/test_fastapi_recovery_integration.py
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "desktop-test-reports" / "fastapi-recovery"

probe_path = Path(__file__).with_name("test_fastapi_startup.py")
spec = importlib.util.spec_from_file_location("aicar_fastapi_probe_helpers", probe_path)
assert spec is not None and spec.loader is not None
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def wait_until(predicate, timeout_seconds: float, interval: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return bool(predicate())


def execute() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report_file = OUT / "source-integration.json"
    log_file = OUT / "source-backend.log"
    sandbox = Path(tempfile.mkdtemp(prefix="aicar-recovery-"))
    port = helper.ephemeral_port()
    tracked = (
        "APPDATA", "DATABASE_URL", "AI_CAR_USE_LOCAL_DATABASE",
        "AI_CAR_BACKEND_HOST", "AI_CAR_BACKEND_PORT", "AI_CAR_BACKEND_URL",
        "AI_CAR_DISABLE_LLM_AUTOSTART", "AI_CAR_BACKEND_STARTUP_TIMEOUT",
        "NO_PROXY", "no_proxy",
    )
    original_env = {key: os.environ.get(key) for key in tracked}
    started = time.monotonic()
    report = {
        "status": "FAIL",
        "scenario": "real FastAPI child termination -> recovery supervisor restart",
        "mode": "source",
        "port": port,
        "health_before_crash": False,
        "original_pid": None,
        "replacement_pid": None,
        "health_after_recovery": False,
        "supervisor_exhausted": None,
        "cleanup": "PENDING",
        "errors": [],
        "log": str(log_file.relative_to(ROOT)),
    }
    desktop_main = None
    supervisor = None

    try:
        os.environ.update({
            "APPDATA": str(sandbox),
            "DATABASE_URL": "sqlite:///" + (sandbox / "diagnostic.sqlite").as_posix(),
            "AI_CAR_USE_LOCAL_DATABASE": "1",
            "AI_CAR_BACKEND_HOST": "127.0.0.1",
            "AI_CAR_BACKEND_PORT": str(port),
            "AI_CAR_BACKEND_URL": f"http://127.0.0.1:{port}",
            "AI_CAR_DISABLE_LLM_AUTOSTART": "1",
            "AI_CAR_BACKEND_STARTUP_TIMEOUT": "90",
            "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        })

        from apps.desktop import main as desktop_main
        from apps.desktop.backend_recovery import BackendRecoverySupervisor

        if not desktop_main.LOCAL_BACKEND or desktop_main.PORT != port:
            raise AssertionError("Launcher is not configured for the isolated test port")

        original = desktop_main.start_backend()
        if original is None or original.poll() is not None:
            raise AssertionError("Desktop did not start and own its FastAPI child")
        report["original_pid"] = original.pid

        report["health_before_crash"] = helper.is_healthy(port)
        if not report["health_before_crash"]:
            raise AssertionError("Real /health never became healthy before crash")

        supervisor = BackendRecoverySupervisor(
            process=lambda: desktop_main._backend_process,
            restart=desktop_main.start_backend,
            healthy=desktop_main._backend_healthy,
            poll_seconds=1.0,
            max_restarts=3,
            window_seconds=120,
        )
        if not supervisor.start():
            raise AssertionError("Recovery supervisor did not start")

        # Kill only the Popen PID we created; do not shut down any other API.
        helper.stop_child(original, frozen=False)
        if original.poll() is None:
            raise AssertionError("Original FastAPI child did not stop")

        def recovered() -> bool:
            current = desktop_main._backend_process
            if current is None or current is original or current.poll() is not None:
                return False
            if current.pid == original.pid:
                return False
            if not helper.is_healthy(port):
                return False
            report["replacement_pid"] = current.pid
            return True

        report["health_after_recovery"] = wait_until(recovered, 100)
        report["supervisor_exhausted"] = supervisor.exhausted
        if not report["health_after_recovery"]:
            raise AssertionError("FastAPI did not auto-restart and restore /health")
        if supervisor.exhausted:
            raise AssertionError("Recovery exhausted its attempt budget")

        report["status"] = "PASS"
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        report["traceback"] = traceback.format_exc(limit=12)
    finally:
        if supervisor is not None:
            supervisor.stop(join_timeout=100)
            if supervisor._thread is not None and supervisor._thread.is_alive():
                report["status"] = "FAIL"
                report["errors"].append("Recovery thread did not stop before cleanup")
        if desktop_main is not None:
            try:
                desktop_main.stop_backend()
            except Exception as exc:
                report["status"] = "FAIL"
                report["errors"].append(f"Local backend shutdown failed: {exc}")

        source_log = sandbox / "AI-Car-Scanner" / "backend.log"
        if source_log.exists():
            try:
                shutil.copyfile(source_log, log_file)
            except OSError as exc:
                report["errors"].append(f"Could not copy backend log: {exc}")
        for key, old_value in original_env.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value

        try:
            helper.cleanup_temporary_database(sandbox, attempts=15)
            report["cleanup"] = "PASS"
        except OSError as exc:
            report["cleanup"] = "FAIL"
            report["status"] = "FAIL"
            report["errors"].append(
                f"Temporary SQLite cleanup blocked: {exc}. Sandbox: {sandbox}"
            )

        report["elapsed_seconds"] = round(time.monotonic() - started, 2)
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            f"[FASTAPI-RECOVERY] {report['status']} | "
            f"crashed_pid={report['original_pid']} "
            f"restarted_pid={report['replacement_pid']} "
            f"health={report['health_after_recovery']} "
            f"cleanup={report['cleanup']}",
            flush=True,
        )
        print(f"[FASTAPI-RECOVERY] Evidence: {report_file}", flush=True)
        if report["status"] != "PASS":
            for error in report["errors"]:
                print(f"[FASTAPI-RECOVERY] FAIL: {error}", flush=True)

    return 0 if report["status"] == "PASS" and report["cleanup"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(execute())
