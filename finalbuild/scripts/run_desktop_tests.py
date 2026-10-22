"""Run the complete Desktop regression matrix in isolated pytest processes.

Usage (from finalbuild/):
    python scripts/run_desktop_tests.py
    python scripts/run_desktop_tests.py --group negative
    python scripts/run_desktop_tests.py --min-coverage 90

A process per group isolates Qt lifecycle issues between UI/widget tests.
The diagnostic-e2e group exercises actual FastAPI routes with an in-process
Desktop transport adapter, without a running network backend.
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
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
# Product runtime modules. Debug probes and PyInstaller-only hooks are still
# included in the full-inventory number, but not the production-core subtotal.
PRODUCTION_MODULES = frozenset({
    "api_client.py", "models.py", "storage.py", "main.py",
    "backend_worker.py", "ui.py", "prepare_windows_icon.py",
    "stage_windows_icons.py", "verify_icons.py",
    "vehicle_artwork.py", "backend_recovery.py",
})
GROUPS = {
    "logic": (
        "apps/desktop/test_smoke.py",
        "apps/desktop/tests",
        "tests/desktop",
        "--ignore=apps/desktop/tests/test_ui_pom.py",
        "--ignore=apps/desktop/tests/test_ui_widgets.py",
        "--ignore=apps/desktop/tests/test_negative_api_contract.py",
        "--ignore=apps/desktop/tests/test_negative_storage.py",
        "--ignore=apps/desktop/tests/test_verify_icons_negative.py",
        "--ignore=apps/desktop/tests/test_real_backend_diagnostic_e2e.py",
    ),
    "diagnostic-e2e": (
        "apps/desktop/tests/test_real_backend_diagnostic_e2e.py",
    ),
    "negative": (
        "apps/desktop/tests/test_negative_api_contract.py",
        "apps/desktop/tests/test_negative_storage.py",
        "apps/desktop/tests/test_verify_icons_negative.py",
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
    # Phase 3 exercises the real API in offline/in-memory mode. Prevent a
    # shell DATABASE_URL from triggering SQLAlchemy create_all() on a remote
    # Postgres instance even if pytest plugins import api.main during collect.
    if name == "diagnostic-e2e":
        env = env.copy()
        env.pop("DATABASE_URL", None)
        print("[DESKTOP] diagnostic-e2e: external database disabled", flush=True)
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
    cases = {}
    if junit.is_file():
        try:
            xml_root = ElementTree.parse(junit).getroot()
            suite = xml_root.find("testsuite") if xml_root.tag == "testsuites" else xml_root
            if suite is not None:
                cases = {
                    label: int(suite.attrib.get(attribute, "0"))
                    for label, attribute in (
                        ("total", "tests"), ("failed", "failures"),
                        ("errors", "errors"), ("skipped", "skipped"),
                    )
                }
                cases["passed"] = max(
                    0, cases["total"] - cases["failed"] - cases["errors"] - cases["skipped"]
                )
        except (OSError, ValueError, ElementTree.ParseError) as exc:
            print(f"[DESKTOP] {name}: could not parse JUnit summary: {exc}", flush=True)
    if cases:
        print(f"[DESKTOP] {name} cases: {cases}", flush=True)
    return {
        "name": name, "status": state, "returncode": code,
        "duration_seconds": duration, "cases": cases,
        "log": str(log.relative_to(ROOT)),
        "junit_xml": str(junit.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group", choices=("all", *GROUPS), default="all",
        help="Run a single independent test group or all five",
    )
    parser.add_argument(
        "--min-coverage", type=float, default=0.0,
        help="Optional combined Desktop coverage gate (0 disables, 90 is the target)",
    )
    parser.add_argument(
        "--min-core-coverage", type=float, default=0.0,
        help="Optional coverage gate for production runtime modules (separate from all-source coverage)",
    )
    parser.add_argument("--reports-dir", default="desktop-test-reports")
    args = parser.parse_args()
    if not 0 <= args.min_coverage <= 100:
        parser.error("--min-coverage must be between 0 and 100")
    if not 0 <= args.min_core_coverage <= 100:
        parser.error("--min-core-coverage must be between 0 and 100")

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
    core_percent = None
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
            # Preserve the complete inventory: low-coverage production code
            # stays in the denominator instead of silently excluding files.
            data = json.loads(summary_file.read_text(encoding="utf-8"))
            per_file = []
            for filename, record in data.get("files", {}).items():
                counts = record.get("summary", {})
                missed = counts.get("missing_lines", 0)
                statements = counts.get("num_statements", 0)
                if not statements:
                    continue
                per_file.append({
                    "file": filename,
                    "statements": statements,
                    "missing": missed,
                    "coverage": round(counts.get("percent_covered", 0), 2),
                    "missing_lines": record.get("missing_lines", []),
                })
            per_file.sort(key=lambda row: (-row["missing"], row["file"]))
            core = [
                row for row in per_file
                if row["file"].replace("\\", "/").startswith("apps/desktop/")
                and row["file"].replace("\\", "/").rsplit("/", 1)[-1] in PRODUCTION_MODULES
            ]
            if core:
                total = sum(row["statements"] for row in core)
                missing = sum(row["missing"] for row in core)
                core_percent = round((total - missing) * 100 / total, 2) if total else None
                print(
                    f"[DESKTOP] Production core source coverage: {core_percent}% "
                    f"({len(core)}/{len(PRODUCTION_MODULES)} modules, target >=90%)"
                )
            # Never pass a production-core gate with missing modules.
            if len(core) != len(PRODUCTION_MODULES):
                core_percent = None
                print("[DESKTOP] Production core coverage incomplete: expected "
                      f"{len(PRODUCTION_MODULES)} module reports; found {len(core)}")
            coverage_gaps = reports / "coverage-gaps.json"
            coverage_gaps.write_text(
                json.dumps(per_file, indent=2) + "\n", encoding="utf-8"
            )
            print("[DESKTOP] Largest uncovered source modules:")
            for item in per_file[:15]:
                line_preview = item["missing_lines"][:18]
                print(f"  {item['file']}: {item['coverage']}%, "
                      f"missing={item['missing']}/{item['statements']}, "
                      f"lines={line_preview}", flush=True)
            print(f"[DESKTOP] Full file-by-file gaps: {coverage_gaps}")
    if percent is None:
        print("[DESKTOP] No coverage result available.")

    if args.min_coverage and (percent is None or percent < args.min_coverage):
        print(f"[DESKTOP] Coverage gate FAIL: {percent} < {args.min_coverage}")
        results.append({"name": "coverage-gate", "status": "FAIL", "threshold": args.min_coverage})
    if args.min_core_coverage and (core_percent is None or core_percent < args.min_core_coverage):
        print(f"[DESKTOP] Production core coverage gate FAIL: {core_percent} < {args.min_core_coverage}")
        results.append({"name": "core-coverage-gate", "status": "FAIL",
                        "threshold": args.min_core_coverage})
    passed = sum(entry["status"] == "PASS" for entry in results)
    failures = sum(entry["status"] != "PASS" for entry in results)
    data = {
        "status": "PASS" if failures == 0 else "FAIL",
        "group_results": results,
        "passed_groups": passed,
        "failed_groups": failures,
        "combined_coverage_percent": percent,
        "production_core_coverage_percent": core_percent,
        "production_module_names": sorted(PRODUCTION_MODULES),
        "coverage_target_percent": 90,
        "coverage_gate_applied_percent": args.min_coverage,
        "core_coverage_gate_applied_percent": args.min_core_coverage,
        "report_dir": str(reports),
    }
    summary = reports / "summary.json"
    summary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"[DESKTOP] OVERALL: {data['status']} / report: {summary}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
