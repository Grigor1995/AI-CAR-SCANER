#!/usr/bin/env bash
# One-command LOCAL Desktop v1.0 release-candidate automated verification.
# Default: source 90% gates + fresh packaged EXE + smoke + performance + visible UI.
# Usage:
#   bash scripts/windows_test_runner.sh
#   bash scripts/windows_test_runner.sh --reuse-exe  # faster; build freshness unverified
#   bash scripts/windows_test_runner.sh --source-only # no EXE, not a release gate
set -Eeuo pipefail
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) echo '[ERROR] Run on an unlocked Windows desktop, using Git Bash.' >&2; exit 2 ;;
esac
cd "$(dirname "$0")/.."

MODE=full
case "${1:-}" in
  "") ;;
  --reuse-exe) MODE=reuse ;;
  --source-only) MODE=source ;;
  *) echo 'Usage: bash scripts/windows_test_runner.sh [--reuse-exe|--source-only]' >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo '[ERROR] Too many options.' >&2; exit 2; }

# Do not implicitly pull or push, modify user settings, or run CI/CD.
STARTED_AT="$(date +%s)"
args=(--coverage-90 --core-coverage-90 --with-performance --with-real-ui --hold-seconds 8)
case "$MODE" in
  full) args+=(--with-exe) ;;
  reuse) args+=(--with-exe --reuse-exe) ;;
  source) echo '[WARN] Source-only run cannot certify Desktop v1.0 packaging.' ;;
esac
bash scripts/run_full_desktop_qa_git_bash.sh "${args[@]}"

if [[ -n "${AI_CAR_DESKTOP_VENV:-}" ]]; then
  PY="$(cygpath -u "$AI_CAR_DESKTOP_VENV")/Scripts/python.exe"
else
  PY="$(cygpath -u "$VIRTUAL_ENV")/Scripts/python.exe"
fi
"$PY" scripts/desktop_v1_readiness.py --mode "$MODE" --since "$STARTED_AT"
echo '[DESKTOP-V1] Automated checks completed; manual acceptance remains PENDING.'
echo '[DESKTOP-V1] Review desktop-test-reports/release-v1-readiness.json and real-ui-acceptance/report.html'
