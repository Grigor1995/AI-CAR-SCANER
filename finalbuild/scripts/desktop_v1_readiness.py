#!/usr/bin/env python3
"""Aggregate FRESH local Desktop v1.0 automated evidence, never approve manual GO."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'desktop-test-reports'
EXE = ROOT / 'dist-release/icon-preview/AICarScanner.exe'


def read_fresh(path: Path, since: int) -> dict:
    if not path.is_file():
        raise RuntimeError(f'Missing report: {path}')
    if path.stat().st_mtime < since - 3:  # protect against stale reports / coarse NTFS timestamps
        raise RuntimeError(f'Report is stale: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=('full', 'reuse', 'source'), required=True)
    p.add_argument('--since', type=int, required=True)
    a = p.parse_args()
    issues = []
    inputs = {}
    for key, path in (
        ('desktop_suite', REPORT/'summary.json'),
        ('performance', REPORT/'performance.json'),
        ('visible_ui', REPORT/'real-ui-acceptance/results.json'),
    ):
        try:
            inputs[key] = read_fresh(path, a.since)
        except (OSError, ValueError, RuntimeError) as exc:
            issues.append(str(exc))
    suite = inputs.get('desktop_suite', {})
    perf = inputs.get('performance', {})
    visible = inputs.get('visible_ui', {})
    core = suite.get('production_core_coverage_percent')
    source = suite.get('combined_coverage_percent')
    if suite.get('status') != 'PASS' or source is None or source < 90 or core is None or core < 90:
        issues.append('Source test suite and both >=90% coverage gates must PASS')
    if perf.get('status') != 'PASS' or perf.get('violations'):
        issues.append('Local Qt navigation/event-loop performance gates must PASS')
    budgets = perf.get('performance_budget_ms') or {}
    if budgets.get('navigation_p95') != 25 or budgets.get('qt_timer_p95') != 2:
        issues.append('Performance gates must use navigation p95 <=25ms and event-loop p95 <=2ms')
    if visible.get('status') != 'PASS' or visible.get('failed') != 0 or not visible.get('tests_total'):
        issues.append('Visible UI automated acceptance must PASS')
    packaged = a.mode != 'source'
    hash_value = None
    if packaged:
        frozen = perf.get('packaged_exe') or {}
        if frozen.get('status') != 'PASS' or frozen.get('repetitions') != 3 or frozen.get('passed') != 3:
            issues.append('Frozen EXE 3/3 stability gate must PASS')
        if not any(c.get('mode') == 'frozen-exe' and c.get('status') == 'PASS' for c in visible.get('cases', [])):
            issues.append('Visible packaged EXE startup/screenshot/shutdown evidence missing')
        for suffix in ('baseline', 'fusion-cleanup'):
            try:
                result = read_fresh(REPORT / f'packaged-{suffix}-result.json', a.since)
                if result.get('status') != 'PASS' or result.get('returncode') != 0:
                    issues.append(f'Frozen {suffix} lifecycle smoke failed')
            except (OSError, ValueError, RuntimeError) as exc:
                issues.append(str(exc))
        if EXE.is_file():
            with EXE.open('rb') as source_exe:
                hash_value = hashlib.file_digest(source_exe, 'sha256').hexdigest()
        else:
            issues.append(f'Missing executable: {EXE}')
        # The runner verifies icon report during a fresh build; reused bundles
        # must never be described as built from the current main source.
        if a.mode == 'full':
            try:
                icons = read_fresh(ROOT / 'dist-release/icon-preview/desktop-icon-report.json', a.since)
                if icons.get('status') != 'PASS':
                    issues.append('Fresh build icon verification failed')
            except (OSError, ValueError, RuntimeError) as exc:
                issues.append(str(exc))
    sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                         capture_output=True, check=False)
    result = {
        'title': 'AI-CAR-SCANER Desktop v1.0 Local Release Candidate',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'git_commit': sha.stdout.strip() if sha.returncode == 0 else 'unknown',
        'mode': a.mode,
        'automated_status': 'FAIL' if issues else ('PASS' if packaged else 'SOURCE_ONLY_PASS'),
        'manual_acceptance': 'PENDING',
        'release_decision': 'NOT_YET_GO',
        'tests_passed': sum(int(r.get('cases', {}).get('passed', 0)) for r in suite.get('group_results', [])),
        'all_source_coverage_percent': source,
        'production_core_coverage_percent': core,
        'qt_navigation_p95_ms': (perf.get('source_qt') or {}).get('navigation_latency', {}).get('p95_ms'),
        'qt_event_loop_p95_ms': (perf.get('source_qt') or {}).get('qt_timer_turnaround', {}).get('p95_ms'),
        'packaged_exe_sha256': hash_value,
        'visible_ui_cases': visible.get('tests_total'),
        'issues': issues,
        'evidence_paths': ['desktop-test-reports/summary.json',
                           'desktop-test-reports/performance.json',
                           'desktop-test-reports/real-ui-acceptance/results.json',
                           'desktop-test-reports/real-ui-acceptance/report.html'],
        'limitations': 'Fake GUI/backend tests do not validate production FastAPI/LLM/OBD; manual review is mandatory.',
    }
    REPORT.mkdir(parents=True, exist_ok=True)
    path = REPORT / 'release-v1-readiness.json'
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"[DESKTOP-V1] {result['automated_status']} | source={source}% core={core}% | tests={result['tests_passed']}")
    print(f'[DESKTOP-V1] Evidence: {path}')
    for msg in issues:
        print(f'[DESKTOP-V1] FAIL: {msg}')
    print('[DESKTOP-V1] Manual acceptance: PENDING, no release tag created')
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
