#!/usr/bin/env bash
# Run frozen onedir GUI with native crash diagnostics, all in Git Bash.
# Usage: bash scripts/run_debug_desktop_git_bash.sh [--native-icon]
set -Eeuo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
EXE="$ROOT/dist-debug/AICarScannerDebug/AICarScannerDebug.exe"
LOG="$ROOT/dist-debug/desktop-run.log"
FAULT="$ROOT/dist-debug/python-faults.log"
if [[ ! -f "$EXE" ]]; then
  echo "[ERROR] Debug executable not built. Run: bash scripts/debug_desktop_git_bash.sh" >&2
  exit 2
fi
export AI_CAR_BACKEND_URL=https://ai-car-scaner.onrender.com
export AI_CAR_DISABLE_LLM_AUTOSTART=1
export QT_DEBUG_PLUGINS=1
export PYTHONFAULTHANDLER=1
export AI_CAR_DEBUG_FAULT_LOG="$(cygpath -w "$FAULT")"
unset QT_QPA_PLATFORM QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH QT_QPA_FONTDIR
export AI_CAR_DISABLE_NATIVE_TASKBAR_ICON=1
export AI_CAR_EARLY_QTCORE=0
for option in "$@"; do
  case "$option" in
    --native-icon) export AI_CAR_DISABLE_NATIVE_TASKBAR_ICON=0 ;;
    --early-qtcore) export AI_CAR_EARLY_QTCORE=1 ;;
    *) echo "Usage: bash scripts/run_debug_desktop_git_bash.sh [--early-qtcore] [--native-icon]" >&2; exit 2 ;;
  esac
done
echo "[DIAG] Launching onedir GUI. Close its window normally when finished."
echo "[DIAG] Early QtCore before cryptography hook: $AI_CAR_EARLY_QTCORE"
echo "[DIAG] Native ctypes icon enabled: $([[ "$AI_CAR_DISABLE_NATIVE_TASKBAR_ICON" == 0 ]] && echo yes || echo no)"
set +e
"$EXE" > "$LOG" 2>&1
rc=$?
set -e
echo "[DIAG] GUI exit status: $rc"
echo "[DIAG] Last console/plugin messages: $LOG"
tail -n 90 "$LOG" || true
if [[ -s "$FAULT" ]]; then
  echo "[DIAG] Last Python fault-handler messages: $FAULT"
  tail -n 65 "$FAULT" || true
fi
echo "[DIAG] In Windows, an access violation often surfaces as 3221225477 / 0xC0000005, or status 139."
exit "$rc"
