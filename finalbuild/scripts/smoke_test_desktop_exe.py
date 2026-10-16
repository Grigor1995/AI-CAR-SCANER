"""Smoke-test the actual frozen Windows Desktop EXE, including clean shutdown.

No real backend, LLM, OBD adapter, or internet required. The local mock HTTP
server handles health and device discovery while a test-only Qt timer closes
the frozen app. The release EXE must exit 0 and emit all lifecycle markers.
"""
from __future__ import annotations

import argparse
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exe",
        default="dist-release/icon-preview/AICarScanner.exe",
        help="Path to a Windows frozen Desktop executable, relative to finalbuild",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--auto-close-ms", type=int, default=2500)
    parser.add_argument("--fusion", action="store_true")
    parser.add_argument("--explicit-cleanup", action="store_true")
    parser.add_argument("--reports-dir", default="desktop-test-reports")
    args = parser.parse_args()
    exe = (ROOT / args.exe).resolve()
    if sys.platform != "win32":
        parser.error("Packaged Desktop smoke test requires Windows")
    if not exe.is_file():
        parser.error(f"Frozen executable not found: {exe}")
    if args.timeout < 5 or args.auto_close_ms < 200 or args.auto_close_ms > 30000:
        parser.error("timeout >=5 and auto-close-ms within 200..30000 required")

    report_dir = (ROOT / args.reports_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    tag = "fusion-cleanup" if args.fusion and args.explicit_cleanup else (
        "fusion" if args.fusion else "explicit-cleanup" if args.explicit_cleanup else "baseline"
    )
    trace_path = report_dir / f"packaged-{tag}-shutdown.log"
    console_path = report_dir / f"packaged-{tag}-console.log"
    result_path = report_dir / f"packaged-{tag}-result.json"
    trace_path.write_text("", encoding="utf-8")
    hits: Counter[str] = Counter()
    guard = threading.Lock()

    class MockDesktopApi(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            with guard:
                hits[path] += 1
            if path == "/health":
                body = {"status": "ok"}
            elif path == "/api/v1/devices":
                body = {"devices": []}
            elif path == "/api/v1/vehicle-catalog/entries":
                body = []
            else:
                self.send_error(404, "unknown mock endpoint")
                return
            data = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args):
            return

    with tempfile.TemporaryDirectory(prefix="ai-car-desktop-smoke-") as temp:
        server = ThreadingHTTPServer(("127.0.0.1", 0), MockDesktopApi)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        env = os.environ.copy()
        env["APPDATA"] = temp
        env["AI_CAR_BACKEND_URL"] = f"http://127.0.0.1:{server.server_port}"
        env["AI_CAR_DISABLE_LLM_AUTOSTART"] = "1"
        env["AI_CAR_TEST_AUTOCLOSE_MS"] = str(args.auto_close_ms)
        env["AI_CAR_SHUTDOWN_TRACE_PATH"] = str(trace_path)
        env["AI_CAR_DISABLE_NATIVE_TASKBAR_ICON"] = "1"
        env["QT_QPA_PLATFORM"] = "offscreen"
        env["QT_DEBUG_PLUGINS"] = "0"
        if args.fusion:
            env["QT_STYLE_OVERRIDE"] = "Fusion"
        else:
            env.pop("QT_STYLE_OVERRIDE", None)
        env["AI_CAR_QT_EXPLICIT_CLEANUP"] = "1" if args.explicit_cleanup else "0"
        env.pop("PYTHONHOME", None)
        env.pop("PYTHONPATH", None)
        start = time.monotonic()
        returncode = None
        timeout_happened = False
        try:
            with console_path.open("wb") as output:
                completed = subprocess.run(
                    [str(exe)], cwd=exe.parent, env=env,
                    stdout=output, stderr=subprocess.STDOUT,
                    timeout=args.timeout, check=False,
                )
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timeout_happened = True
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        elapsed = round(time.monotonic() - start, 2)

    trace = trace_path.read_text(encoding="utf-8", errors="replace")
    with guard:
        hit_counts = dict(hits)
    required_markers = (
        "smoke: main_window_shown",
        "ui: QApplication.exec returned rc=0",
        "ui: returning to main.run",
        "main: backend/LLM cleanup complete",
    )
    missing = [marker for marker in required_markers if marker not in trace]
    missing_http = [path for path in ("/health", "/api/v1/devices") if not hit_counts.get(path)]
    success = returncode == 0 and not timeout_happened and not missing and not missing_http
    summary = {
        "status": "PASS" if success else "FAIL",
        "executable": str(exe),
        "variant": tag,
        "returncode": returncode,
        "timeout": timeout_happened,
        "elapsed_seconds": elapsed,
        "mock_backend_requests": hit_counts,
        "missing_lifecycle_markers": missing,
        "missing_mock_requests": missing_http,
        "trace_file": str(trace_path),
        "console_file": str(console_path),
    }
    result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[DESKTOP-EXE] {tag}: {summary['status']} exit={returncode}, elapsed={elapsed}s")
    print(f"[DESKTOP-EXE] Mock API: {hit_counts}")
    print(f"[DESKTOP-EXE] Trace: {trace_path}")
    if not success:
        print(f"[DESKTOP-EXE] Missing lifecycle markers: {missing}")
        print(f"[DESKTOP-EXE] Missing API requests: {missing_http}")
        print("\n".join(console_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
