#!/usr/bin/env bash
# Standalone visible UI acceptance. Does not run source coverage or rebuild EXE.
set -Eeuo pipefail
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) echo '[ERROR] Requires visible Windows desktop and Git Bash.' >&2; exit 2 ;;
esac
cd "$(dirname "$0")/.."
if [[ -n "${AI_CAR_DESKTOP_VENV:-}" ]]; then
  PY="$(cygpath -u "$AI_CAR_DESKTOP_VENV")/Scripts/python.exe"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
  PY="$(cygpath -u "$VIRTUAL_ENV")/Scripts/python.exe"
else
  echo '[ERROR] Activate the Python 3.14 .venv first.' >&2; exit 2
fi
[[ -f "$PY" ]] || { echo "[ERROR] Python missing: $PY" >&2; exit 2; }
EXE='dist-release/icon-preview/AICarScanner.exe'
case "${1:-}" in
  --source-only) env -u QT_QPA_PLATFORM -u QT_STYLE_OVERRIDE "$PY" scripts/real_ui_acceptance.py --mode source --hold-seconds 8 ;;
  "")
    [[ -s "$EXE" ]] || { echo "[ERROR] Missing $EXE; build with bash scripts/build_desktop_git_bash.sh, or use --source-only." >&2; exit 4; }
    env -u QT_QPA_PLATFORM -u QT_STYLE_OVERRIDE "$PY" scripts/real_ui_acceptance.py --mode all --exe "$EXE" --hold-seconds 8 ;;
  *) echo 'Usage: bash scripts/run_real_ui_v1_git_bash.sh [--source-only]' >&2; exit 2 ;;
esac
