#!/usr/bin/env bash
# Local Windows 11/Python 3.14 Desktop QA and optional release v1 visual gates.
# No GitHub Actions or CI/CD invocation. Run from any directory:
#   bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90 --core-coverage-90
#   bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90 --with-exe --with-performance --with-real-ui
#   bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90 --with-exe --reuse-exe --with-performance --with-real-ui
set -Eeuo pipefail
trap 'code=$?; echo "[DESKTOP-QA] Failed at line $LINENO (exit $code)" >&2' ERR

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) echo "[ERROR] Use Git Bash on Windows x64." >&2; exit 2 ;;
esac
cd "$(dirname "$0")/.."

WITH_EXE=0
REUSE_EXE=0
WITH_PERFORMANCE=0
WITH_REAL_UI=0
MIN_COVERAGE=0
MIN_CORE_COVERAGE=0
HOLD_SECONDS=8
EXE_PATH="dist-release/icon-preview/AICarScanner.exe"
usage() {
  echo "Usage: bash scripts/run_full_desktop_qa_git_bash.sh [--coverage-90] [--core-coverage-90] [--with-exe] [--reuse-exe] [--with-performance] [--with-real-ui] [--hold-seconds N]" >&2
}
while (($#)); do
  case "$1" in
    --with-exe) WITH_EXE=1 ;;
    --reuse-exe) REUSE_EXE=1 ; WITH_EXE=1 ;;
    --with-performance) WITH_PERFORMANCE=1 ;;
    --with-real-ui) WITH_REAL_UI=1 ;;
    --coverage-90) MIN_COVERAGE=90 ;;
    --core-coverage-90) MIN_CORE_COVERAGE=90 ;;
    --hold-seconds)
      (($# >= 2)) || { usage; exit 2; }
      HOLD_SECONDS="$2"
      shift ;;
    *) usage; exit 2 ;;
  esac
  shift
done

if [[ -n "${AI_CAR_DESKTOP_VENV:-}" ]]; then
  PY="$(cygpath -u "$AI_CAR_DESKTOP_VENV")/Scripts/python.exe"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
  PY="$(cygpath -u "$VIRTUAL_ENV")/Scripts/python.exe"
else
  echo "[ERROR] Activate Python 3.14 .venv or set AI_CAR_DESKTOP_VENV." >&2
  exit 2
fi
[[ -f "$PY" ]] || { echo "[ERROR] Venv Python not found: $PY" >&2; exit 2; }
"$PY" -c 'import sys; assert sys.platform == "win32" and sys.version_info[:2] == (3,14), sys.version'
"$PY" -c 'import sys; assert sys.prefix != sys.base_prefix, "Expected a Python virtual environment"'
"$PY" - "$HOLD_SECONDS" <<'PYCODE'
import sys
try:
    hold = float(sys.argv[1])
except ValueError as e:
    raise SystemExit(f"Invalid --hold-seconds: {e}")
if not 0 <= hold <= 60:
    raise SystemExit("--hold-seconds must be 0..60")
PYCODE

echo "[DESKTOP-QA] Python 3.14 venv: $PY"
"$PY" scripts/run_desktop_tests.py --min-coverage "$MIN_COVERAGE" --min-core-coverage "$MIN_CORE_COVERAGE"

if [[ "$WITH_EXE" -eq 1 ]]; then
  if [[ "$REUSE_EXE" -eq 0 ]]; then
    echo "[DESKTOP-QA] Building fresh Windows release candidate (staged artwork)..."
    bash scripts/build_desktop_git_bash.sh
  else
    echo "[DESKTOP-QA] Reusing existing EXE. Note: this is NOT proof of a fresh main-commit build."
  fi
  [[ -s "$EXE_PATH" ]] || { echo "[ERROR] Missing EXE: $EXE_PATH" >&2; exit 4; }
  echo "[DESKTOP-QA] Testing real frozen EXE with isolated local mock API..."
  "$PY" scripts/smoke_test_desktop_exe.py --exe "$EXE_PATH"
  "$PY" scripts/smoke_test_desktop_exe.py --exe "$EXE_PATH" --fusion --explicit-cleanup
fi

if [[ "$WITH_PERFORMANCE" -eq 1 ]]; then
  echo "[DESKTOP-QA] Performance gates: navigation p95 <=25ms; Qt event p95 <=2ms."
  PERF_ARGS=(--iterations 100 --max-navigation-p95-ms 25 --max-qt-p95-ms 2)
  if [[ "$WITH_EXE" -eq 1 ]]; then
    PERF_ARGS+=(--exe "$EXE_PATH" --exe-runs 3)
  fi
  "$PY" scripts/benchmark_desktop.py "${PERF_ARGS[@]}"
fi

if [[ "$WITH_REAL_UI" -eq 1 ]]; then
  [[ -f scripts/real_ui_acceptance.py ]] || { echo "[ERROR] Missing scripts/real_ui_acceptance.py" >&2; exit 4; }
  # Real native QWidget interaction requires a visible, unlocked Windows desktop.
  # Offscreen is used by isolated pytest/performance tests only, never here.
  echo "[DESKTOP-QA] Visible UI acceptance: leave Windows unlocked and do not move the mouse."
  UI_ARGS=(--mode source --hold-seconds "$HOLD_SECONDS")
  if [[ "$WITH_EXE" -eq 1 ]]; then
    UI_ARGS=(--mode all --exe "$EXE_PATH" --hold-seconds "$HOLD_SECONDS")
  fi
  env -u QT_QPA_PLATFORM -u QT_STYLE_OVERRIDE "$PY" scripts/real_ui_acceptance.py "${UI_ARGS[@]}"
fi

echo "[DESKTOP-QA] PASS: all requested phases completed. Reports: desktop-test-reports/"
