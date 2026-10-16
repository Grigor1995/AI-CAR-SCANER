#!/usr/bin/env bash
# Run packaged Windows GUI with isolated shutdown traces.
# Usage: bash scripts/run_debug_desktop_git_bash.sh [--fusion] [--explicit-cleanup]
set -Eeuo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
EXE="$ROOT/dist-debug/AICarScannerDebug/AICarScannerDebug.exe"
if [[ ! -f "$EXE" ]]; then
  echo "[ERROR] Debug executable not built. Run: bash scripts/debug_desktop_git_bash.sh --desktop-only" >&2
  exit 2
fi

export AI_CAR_BACKEND_URL=https://ai-car-scaner.onrender.com
export AI_CAR_DISABLE_LLM_AUTOSTART=1
export PYTHONFAULTHANDLER=1
export QT_DEBUG_PLUGINS="${QT_DEBUG_PLUGINS:-0}"
unset QT_QPA_PLATFORM QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH QT_QPA_FONTDIR
export AI_CAR_DISABLE_NATIVE_TASKBAR_ICON=1
export AI_CAR_EARLY_QTCORE=0
export AI_CAR_QT_EXPLICIT_CLEANUP=0

variant="baseline"
for option in "$@"; do
  case "$option" in
    --fusion)
      export QT_STYLE_OVERRIDE=Fusion
      variant="$variant-fusion"
      ;;
    --explicit-cleanup)
      export AI_CAR_QT_EXPLICIT_CLEANUP=1
      variant="$variant-cleanup"
      ;;
    --early-qtcore)
      export AI_CAR_EARLY_QTCORE=1
      variant="$variant-early"
      ;;
    --native-icon)
      export AI_CAR_DISABLE_NATIVE_TASKBAR_ICON=0
      variant="$variant-native"
      ;;
    *)
      echo "Usage: bash scripts/run_debug_desktop_git_bash.sh [--fusion] [--explicit-cleanup] [--early-qtcore] [--native-icon]" >&2
      exit 2
      ;;
  esac
done
if [[ "$variant" == "baseline" && "${QT_STYLE_OVERRIDE:-}" == "Fusion" ]]; then
  variant="baseline-fusion"
fi

if [[ "$variant" == "baseline" ]]; then
  LOG="$ROOT/dist-debug/desktop-run.log"
else
  LOG="$ROOT/dist-debug/desktop-run-$variant.log"
fi
TRACE="$ROOT/dist-debug/shutdown-trace-$variant.log"
FAULT="$ROOT/dist-debug/python-faults-$variant.log"
: > "$TRACE"
: > "$FAULT"
export AI_CAR_DEBUG_FAULT_LOG="$(cygpath -w "$FAULT")"
export AI_CAR_SHUTDOWN_TRACE_PATH="$(cygpath -w "$TRACE")"

echo "[DIAG] Launching onedir GUI; close the window normally after it opens."
echo "[DIAG] Qt style: ${QT_STYLE_OVERRIDE:-Windows default}"
echo "[DIAG] Explicit Qt cleanup: $AI_CAR_QT_EXPLICIT_CLEANUP"
echo "[DIAG] Early QtCore experiment: $AI_CAR_EARLY_QTCORE"
echo "[DIAG] Native ctypes icon enabled: $([[ "$AI_CAR_DISABLE_NATIVE_TASKBAR_ICON" == 0 ]] && echo yes || echo no)"
set +e
"$EXE" > "$LOG" 2>&1
rc=$?
set -e
echo "[DIAG] GUI exit status: $rc"
echo "[DIAG] Shutdown checkpoints: $TRACE"
cat "$TRACE" || true
echo "[DIAG] Last bootloader and application messages: $LOG"
tail -n 35 "$LOG" || true
if [[ -s "$FAULT" ]]; then
  echo "[DIAG] Current-run Python fault report: $FAULT"
  tail -n 45 "$FAULT" || true
fi
echo "[DIAG] A normal Qt window display alone does not prove clean native shutdown."
exit "$rc"
