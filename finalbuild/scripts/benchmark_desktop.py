"""Phase 4 Desktop latency/stability measurement (offline, non-destructive).

Samples real PySide6 navigation and Qt event-loop scheduling with mocked API
and storage. Optionally runs an actual frozen Windows EXE multiple times using
the existing mock-backend smoke contract. Emits machine-readable evidence.

Usage:
    python scripts/benchmark_desktop.py
    python scripts/benchmark_desktop.py --exe dist-release/icon-preview/AICarScanner.exe --exe-runs 3
    python scripts/benchmark_desktop.py --max-navigation-p95-ms 150 --max-qt-p95-ms 100

WARNING: offscreen PySide6 timing is NOT visible FPS or GPU rendering speed.
Python tracemalloc does NOT account for Qt/C++ allocations/native process RSS.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import tracemalloc
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
# Executing `python scripts/benchmark_desktop.py` puts scripts/, not the
# repository root, at sys.path[0]. Make apps.desktop importable explicitly.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def percentile(values: list[float], target: float) -> float:
    if not values:
        raise ValueError("Performance sample set must not be empty")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * target / 100.0
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    fraction = rank - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def describe_ms(values: list[float]) -> dict[str, float | int]:
    return {
        "samples": len(values),
        "mean_ms": round(statistics.fmean(values), 3),
        "p50_ms": round(percentile(values, 50), 3),
        "p95_ms": round(percentile(values, 95), 3),
        "max_ms": round(max(values), 3),
    }


def benchmark_qt_source(iterations: int) -> dict:
    # Avoid global Qt environment changes in users' regular Desktop launch.
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
    os.environ["AI_CAR_DISABLE_LLM_AUTOSTART"] = "1"
    from PySide6.QtCore import QEventLoop, QTimer, QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    from apps.desktop import ui

    class EphemeralSettings:
        def __init__(self, *_args):
            pass

        def value(self, _name, default=None, type=None):
            return default
        def setValue(self, *_args):
            pass

    class EmptyStore:
        def load(self):
            return []
        def save(self, _profiles):
            raise AssertionError("Benchmark must never write real vehicle profiles")

    class NoNetworkAPI:
        base_url = "http://127.0.0.1:9"  # Inert metadata; no vehicle triggers portrait loading.
        def __getattr__(self, name):
            raise AssertionError(f"Benchmark must never access backend API: {name}")

    app = QApplication.instance() or QApplication([])
    with (
        patch.object(ui, "QSettings", EphemeralSettings),
        patch.object(ui, "VehicleStore", EmptyStore),
        patch.object(ui, "DiagnosticApiClient", NoNetworkAPI),
        patch.object(ui.MainWindow, "refresh_all", lambda self: None),
    ):
        # Exclude module-import/cold setup from the navigation/loop measurements;
        # report the actual window-construction time separately.
        gc.collect()
        tracemalloc.start()
        start_py_bytes, _ = tracemalloc.get_traced_memory()
        startup = time.perf_counter()
        window = ui.MainWindow()
        window.show()
        app.processEvents()
        startup_ms = (time.perf_counter() - startup) * 1000

        nav_samples: list[float] = []
        timer_samples: list[float] = []
        try:
            for cycle in range(iterations):
                before = time.perf_counter()
                window.navigate_page(cycle % len(window.pages))
                app.processEvents()
                nav_samples.append((time.perf_counter() - before) * 1000)

                loop = QEventLoop()
                before = time.perf_counter()
                QTimer.singleShot(0, loop.quit)
                loop.exec()
                timer_samples.append((time.perf_counter() - before) * 1000)
            gc.collect()
            finish_py_bytes, peak_py_bytes = tracemalloc.get_traced_memory()
        finally:
            window.close()
            window.deleteLater()
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
            tracemalloc.stop()

    return {
        "mode": "source-offscreen-no-network",
        "window_startup_ms": round(startup_ms, 3),
        "navigation_latency": describe_ms(nav_samples),
        "qt_timer_turnaround": describe_ms(timer_samples),
        "python_allocated_growth_kib": round((finish_py_bytes - start_py_bytes) / 1024, 3),
        "python_tracemalloc_peak_kib": round(peak_py_bytes / 1024, 3),
        "limitations": (
            "Qt offscreen; no rendering FPS or GPU measurement. "
            "tracemalloc excludes native Qt/C++ memory."
        ),
    }


def benchmark_exe(exe: str, runs: int, reports: Path) -> dict:
    if sys.platform != "win32":
        raise RuntimeError("Frozen EXE stability sampling requires Windows")
    full_exe = (ROOT / exe).resolve()
    if not full_exe.is_file():
        raise FileNotFoundError(f"Frozen Windows GUI EXE not found: {full_exe}")
    results = []
    for index in range(runs):
        test_reports = reports / "packaged-stability" / f"run-{index+1:02}"
        command = [
            sys.executable, str(ROOT / "scripts" / "smoke_test_desktop_exe.py"),
            "--exe", str(full_exe), "--reports-dir", str(test_reports),
            "--timeout", "60", "--auto-close-ms", "1600",
        ]
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=85,
            env={**os.environ, "AI_CAR_DISABLE_LLM_AUTOSTART": "1"},
        )
        report_path = test_reports / "packaged-baseline-result.json"
        report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {
            "status": "FAIL", "returncode": completed.returncode,
            "error": completed.stderr[-2000:],
        }
        results.append(report)
        print(f"[DESKTOP-PERF] Frozen repeat {index+1}/{runs}: "
              f"{report['status']} exit={report.get('returncode')}", flush=True)
    passing = all(x.get("status") == "PASS" and x.get("returncode") == 0 for x in results)
    durations = [x["elapsed_seconds"] * 1000 for x in results if "elapsed_seconds" in x]
    return {
        "status": "PASS" if passing else "FAIL",
        "repetitions": runs,
        "passed": sum(x.get("status") == "PASS" and x.get("returncode") == 0 for x in results),
        "startup_to_close_elapsed_ms": describe_ms(durations) if durations else None,
        "samples": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=70)
    parser.add_argument("--exe", default=None)
    parser.add_argument("--exe-runs", type=int, default=3)
    parser.add_argument("--max-navigation-p95-ms", type=float, default=0.0)
    parser.add_argument("--max-qt-p95-ms", type=float, default=0.0)
    parser.add_argument("--reports-dir", default="desktop-test-reports")
    args = parser.parse_args()
    if args.iterations < 10 or args.exe_runs < 1:
        parser.error("At least 10 navigation iterations and 1 EXE run are required")
    if args.max_navigation_p95_ms < 0 or args.max_qt_p95_ms < 0:
        parser.error("Performance gates must be nonnegative; zero disables a gate")
    if args.exe_runs > 25:
        parser.error("Maximum EXE stability runs per invocation is 25")

    reports = (ROOT / args.reports_dir).resolve()
    reports.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "MEASURED",
        "performance_budget_ms": {
            "navigation_p95": args.max_navigation_p95_ms,
            "qt_timer_p95": args.max_qt_p95_ms,
        },
        "source_qt": benchmark_qt_source(args.iterations),
        "packaged_exe": None,
        "violations": [],
    }
    nav = result["source_qt"]["navigation_latency"]["p95_ms"]
    qt = result["source_qt"]["qt_timer_turnaround"]["p95_ms"]
    if args.max_navigation_p95_ms and nav > args.max_navigation_p95_ms:
        result["violations"].append(f"navigation p95 {nav}ms > {args.max_navigation_p95_ms}ms")
    if args.max_qt_p95_ms and qt > args.max_qt_p95_ms:
        result["violations"].append(f"Qt event-loop p95 {qt}ms > {args.max_qt_p95_ms}ms")

    if args.exe:
        result["packaged_exe"] = benchmark_exe(args.exe, args.exe_runs, reports)
        if result["packaged_exe"]["status"] != "PASS":
            result["violations"].append("Frozen Windows EXE did not exit 0 in every repeat")

    has_gate = bool(
        args.max_navigation_p95_ms or args.max_qt_p95_ms or args.exe
    )
    if result["violations"]:
        result["status"] = "FAIL"
    elif has_gate:
        result["status"] = "PASS"
    # Without any explicit budget or frozen-EXE checks, report MEASURED,
    # not PASS. A successful benchmark invocation is not an SLA verdict.
    path = reports / "performance.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[DESKTOP-PERF] Qt navigation p95: {nav}ms, event-loop p95: {qt}ms")
    print(f"[DESKTOP-PERF] {result['status']} | evidence: {path}")
    for error in result["violations"]:
        print(f"[DESKTOP-PERF] FAIL: {error}")
    return 1 if result["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
