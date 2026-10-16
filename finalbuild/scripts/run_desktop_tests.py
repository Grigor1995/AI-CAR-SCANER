"""Run the complete Desktop regression matrix in isolated pytest processes.

Usage (from finalbuild/):
    python scripts/run_desktop_tests.py
    python scripts/run_desktop_tests.py --group negative
    python scripts/run_desktop_tests.py --min-coverage 90

A process per group isolates Qt lifecycle issues between UI/widget tests.
No physical OBD device, remote API, cloud AI provider or PostgreSQL needed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "logic": (
        "apps/desktop/test_smoke.py",
        "apps/desktop/tests",
        "tests/desktop",
        "--ignore=apps/desktop/tests/test_ui_pom.py",
        "--ignore=apps/desktop/tests/test_ui_widgets.py",
        "--ignore=apps/desktop/tests/test_negative_api_contract.py",
    ),
    "negative": (
        "apps/desktop/tests/test_negative_api_contract.py",
        "apps/desktop/tests/test_negative_storage.py",
    ),
    "ui-pom": ("apps/desktop/tests/test_ui_pom.py",),
    "ui-widgets": ("apps/desktop/tests/test_ui_widgets.py",),
}


def run_group(name: str, arguments: tuple[str, ...], reports: Path, env: dict[str, str]) -> dict:
    junit = reports / f"{name}-junit.xml"
    log = reports / f"{name}.log"
    cmd = [
        sys.executable, "-m", "pytest", "-q",
        "-p", "no:benchmark", "--durations=10",
        f"--junitxml={junit}",
        "--cov=apps.desktop", "--cov-append", "--cov-report=",
        *arguments,
    ]
    print(f"[DESKTOP] Running {name}: {len(arguments)} selection arguments", flush=True)
    start = time.perf_counter()
    try:
        with log.open("w", encoding="utf-8") as output:
            completed = subprocess.run(
                cmd, cwd=ROOT, env=env, stdout=output,
                stderr=subprocess.STDOUT, timeout=600, check=False,
            )
        code, state = completed.returncode, "PASS" if completed.returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        code, state = 124, "TIMEOUT"
        with log.open("a", encoding="utf-8") as output:
            output.write("\nDESKTOP GROUP TIMED OUT AFTER 600 SECONDS\n")
    duration = round(time.perf_counter() - start, 2)
    print(f"[DESKTOP] {name}: {state} (exit={code}, {duration}s)", flush=True)
    if state != "PASS":
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-45:]
        print("\n".join(tail), flush=True)
    return {
        "name": name, "status": state, "returncode": code,
        "duration_seconds": duration,
        "log": str(log.relative_to(ROOT)),
        "junit_xml": str(junit.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group", choices=("all", *GROUPS), default="all",
        help="Run a single independent test group or all four",
    )
    parser.add_argument(
        "--min-coverage", type=float, default=0.0,
        help="Optional combined Desktop coverage gate (0 disables, 90 is the target)",
    )
    parser.add_argument("--reports-dir", default="desktop-test-reports")
    args = parser.parse_args()
    if not 0 <= args.min_coverage <= 100:
        parser.error("--min-coverage must be between 0 and 100")

    reports = (ROOT / args.reports_dir).resolve()
    reports.mkdir(parents=True, exist_ok=True)
    coverage_file = reports / ".coverage"
    if coverage_file.exists():
        coverage_file.unlink()
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_STYLE_OVERRIDE"] = "Fusion"
    env["AI_CAR_DISABLE_LLM_AUTOSTART"] = "1"
    env["COVERAGE_FILE"] = str(coverage_file)
    # No accidental live HTTP requests in tests; all API operations use mocks.
    env.pop("AI_CAR_SHUTDOWN_TRACE_PATH", None)
    env.pop("AI_CAR_TEST_AUTOCLOSE_MS", None)
    env.pop("AI_CAR_QT_EXPLICIT_CLEANUP", None)
    selection = GROUPS if args.group == "all" else {args.group: GROUPS[args.group]}
    results = [run_group(name, items, reports, env) for name, items in selection.items()]

    percent = None
    if coverage_file.exists():
        for fmt, flag, filename in (
            ("XML", "xml", "coverage.xml"),
            ("HTML", "html", "htmlcov"),
            ("JSON", "json", "coverage.json"),
        ):
            cmd = [sys.executable, "-m", "coverage", flag,
                   "-d" if flag == "html" else "-o", str(reports / filename)]
            completed = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
            if completed.returncode != 0:
                print(f"[DESKTOP] Coverage {fmt}: FAIL: {completed.stderr.strip()}")
        summary_file = reports / "coverage.json"
        if summary_file.exists():
            percent = round(
                json.loads(summary_file.read_text(encoding="utf-8"))["totals"]["percent_covered"], 2
            )
            print(f"[DESKTOP] Combined source coverage: {percent}% (target >=90%)")
    if percent is None:
        print("[DESKTOP] No coverage result available.")

    if args.min_coverage and (percent is None or percent < args.min_coverage):
        print(f"[DESKTOP] Coverage gate FAIL: {percent} < {args.min_coverage}")
        results.append({"name": "coverage-gate", "status": "FAIL", "threshold": args.min_coverage})
    passed = sum(entry["status"] == "PASS" for entry in results)
    failures = sum(entry["status"] != "PASS" for entry in results)
    data = {
        "status": "PASS" if failures == 0 else "FAIL",
        "group_results": results,
        "passed_groups": passed,
        "failed_groups": failures,
        "combined_coverage_percent": percent,
        "coverage_target_percent": 90,
        "coverage_gate_applied_percent": args.min_coverage,
        "report_dir": str(reports),
    }
    summary = reports / "summary.json"
    summary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"[DESKTOP] OVERALL: {data['status']} / report: {summary}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
