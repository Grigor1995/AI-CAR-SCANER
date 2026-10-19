#!/usr/bin/env bash
# Full Desktop QA from Windows Git Bash with the existing Python 3.14 venv.
# Usage:
#   bash scripts/run_full_desktop_qa_git_bash.sh
#   bash scripts/run_full_desktop_qa_git_bash.sh --with-exe
#   bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90
#   bash scripts/run_full_desktop_qa_git_bash.sh --core-coverage-90
#   bash scripts/run_full_desktop_qa_git_bash.sh --with-performance
#   bash scripts/run_full_desktop_qa_git_bash.sh --with-exe --with-performance
set -Eeuo pipefail
trap 'code=$?; echo "[DESKTOP-QA] Failed at line $LINENO (exit $code)" >&2' ERR

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) echo "[ERROR] Use Git Bash on Windows x64." >&2; exit 2 ;;
esac
cd "$(dirname "$0")/.."

WITH_EXE=0
WITH_PERFORMANCE=0
MIN_COVERAGE=0
MIN_CORE_COVERAGE=0
for option in "$@"; do
  case "$option" in
    --with-exe) WITH_EXE=1 ;;
    --with-performance) WITH_PERFORMANCE=1 ;;
    --coverage-90) MIN_COVERAGE=90 ;;
    --core-coverage-90) MIN_CORE_COVERAGE=90 ;;
    *) echo "Usage: bash scripts/run_full_desktop_qa_git_bash.sh [--with-exe] [--with-performance] [--coverage-90] [--core-coverage-90]" >&2; exit 2 ;;
  esac
done

if [[ -n "${AI_CAR_DESKTOP_VENV:-}" ]]; then
  PY="$(cygpath -u "$AI_CAR_DESKTOP_VENV")/Scripts/python.exe"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
  PY="$(cygpath -u "$VIRTUAL_ENV")/Scripts/python.exe"
else
  echo "[ERROR] Activate your Python 3.14 .venv or set AI_CAR_DESKTOP_VENV." >&2
  exit 2
fi
if [[ ! -f "$PY" ]]; then
  echo "[ERROR] Could not find venv Python: $PY" >&2; exit 2
fi
"$PY" -c 'import sys; assert sys.platform == "win32" and sys.version_info[:2] == (3,14), sys.version'
echo "[DESKTOP-QA] Python 3.14 venv: $PY"

"$PY" scripts/run_desktop_tests.py --min-coverage "$MIN_COVERAGE" --min-core-coverage "$MIN_CORE_COVERAGE"

if [[ "$WITH_EXE" -eq 1 ]]; then
  echo "[DESKTOP-QA] Build release EXE using isolated staged artwork..."
  bash scripts/build_desktop_git_bash.sh
  echo "[DESKTOP-QA] Smoke real frozen EXE with local mock API..."
  "$PY" scripts/smoke_test_desktop_exe.py \
    --exe dist-release/icon-preview/AICarScanner.exe
  "$PY" scripts/smoke_test_desktop_exe.py \
    --exe dist-release/icon-preview/AICarScanner.exe \
    --fusion --explicit-cleanup
fi

if [[ "$WITH_PERFORMANCE" -eq 1 ]]; then
  echo "[DESKTOP-QA] Measuring real Qt responsiveness (no network/profile writes)..."
  PERF_ARGS=()
  if [[ "$WITH_EXE" -eq 1 ]]; then
    echo "[DESKTOP-QA] Repeating native release EXE smoke to sample shutdown stability..."
    PERF_ARGS+=(--exe dist-release/icon-preview/AICarScanner.exe --exe-runs 3)
  fi
  "$PY" scripts/benchmark_desktop.py "${PERF_ARGS[@]}"
fi
echo "[DESKTOP-QA] PASS. Reports: desktop-test-reports/"
