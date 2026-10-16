#!/usr/bin/env bash
# Diagnostic Windows x64 onedir/console build (preserves production EXE).
# Run from finalbuild: bash scripts/debug_desktop_git_bash.sh
set -Eeuo pipefail
trap 'rc=$?; echo "[FAIL] Debug builder stopped at line $LINENO (code $rc)" >&2' ERR

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) echo "[ERROR] Use Windows Git Bash, not Linux or WSL." >&2; exit 2 ;;
esac

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
DIST="dist-debug"
WORK="build-debug"

echo "[1/6] Locate your already installed Windows Python 3.14 x64 venv"
CANDIDATES=()
if [[ -n "${AI_CAR_DESKTOP_VENV:-}" ]]; then
  CANDIDATES+=("$AI_CAR_DESKTOP_VENV")
else
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then CANDIDATES+=("$VIRTUAL_ENV"); fi
  CANDIDATES+=("apps/desktop/.venv" "Desktop/.venv" ".venv" "../.venv" "$HOME/Desktop/.venv")
fi
PY=""
for candidate in "${CANDIDATES[@]}"; do
  candidate="$(cygpath -u "$candidate")"
  if [[ -f "$candidate/Scripts/python.exe" ]]; then
    if "$candidate/Scripts/python.exe" -c 'import sys,struct; assert sys.version_info[:2]==(3,14) and sys.platform=="win32" and struct.calcsize("P")==8' >/dev/null 2>&1; then
      PY="$candidate/Scripts/python.exe"
      break
    fi
  fi
done
if [[ -z "$PY" ]]; then
  echo "[ERROR] Set AI_CAR_DESKTOP_VENV to your existing Python 3.14 .venv." >&2
  exit 2
fi
"$PY" -c 'import sys,PySide6,shiboken6,PyInstaller; print("Python",sys.version,"PySide6",PySide6.__version__,"Shiboken",shiboken6.__version__,"PyInstaller",PyInstaller.__version__)'

echo "[2/6] Clear Qt environment overrides, write diagnostics only in dist-debug/"
unset QT_QPA_PLATFORM QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH QT_QPA_FONTDIR
export QT_DEBUG_PLUGINS=1
export PYTHONFAULTHANDLER=1
mkdir -p "$DIST" "$WORK"
export AI_CAR_DEBUG_FAULT_LOG="$(cygpath -w "$ROOT/$DIST/python-faults.log")"
echo "[DIAG] Current Qt-related environment:"
env | grep -E '^(QT_|PYTHONPATH|PYTHONHOME)' || true

echo "[DIAG] Verify source assets before invoking PyInstaller"
for asset in \
  assets/AI-Car-Scanner-mobile.png \
  assets/AI-Car-Scanner.webp \
  assets/AI-Car-Scanner.ico \
  shared/vehicle_catalog.json; do
  if [[ ! -f "$ROOT/$asset" ]]; then
    echo "[ERROR] Missing source asset: $ROOT/$asset" >&2
    exit 3
  fi
done

echo "[3/6] Freeze a MINIMAL PySide6 Qt probe as a console + onedir EXE"
"$PY" -m PyInstaller --noconfirm --clean --onedir --console \
  --debug bootloader --name AIQtProbe \
  --distpath "$DIST" --workpath "$WORK/qt" --specpath "$WORK" \
  --paths "$(cygpath -w "$ROOT")" \
  --runtime-hook "$(cygpath -w "$ROOT/apps/desktop/debug_runtime_hook.py")" \
  --add-data "$(cygpath -w "$ROOT/assets/AI-Car-Scanner-mobile.png");assets" \
  "$(cygpath -w "$ROOT/apps/desktop/qt_freeze_probe.py")"

echo "[4/6] Run minimal Qt probe (auto-closes after about one second)"
set +e
"$DIST/AIQtProbe/AIQtProbe.exe" > "$DIST/qt-probe.log" 2>&1
QT_RC=$?
set -e
echo "[DIAG] Qt probe exit status: $QT_RC"
tail -n 45 "$DIST/qt-probe.log" || true
if [[ "$QT_RC" -ne 0 ]]; then
  echo "[WARN] Qt probe failed. Check dist-debug/qt-probe.log and python-faults.log."
fi

echo "[5/6] Freeze ACTUAL Desktop GUI as console + onedir (without overwriting release)"
"$PY" -m PyInstaller --noconfirm --clean --onedir --console \
  --debug bootloader --name AICarScannerDebug \
  --distpath "$DIST" --workpath "$WORK/desktop" --specpath "$WORK" \
  --paths "$(cygpath -w "$ROOT")" \
  --runtime-hook "$(cygpath -w "$ROOT/apps/desktop/debug_runtime_hook.py")" \
  --hidden-import apps.desktop.ui \
  --hidden-import apps.desktop.api_client \
  --add-data "$(cygpath -w "$ROOT/shared/vehicle_catalog.json");shared" \
  --add-data "$(cygpath -w "$ROOT/assets/AI-Car-Scanner.ico");assets" \
  --add-data "$(cygpath -w "$ROOT/assets/AI-Car-Scanner.webp");assets" \
  --add-data "$(cygpath -w "$ROOT/assets/AI-Car-Scanner-mobile.png");assets" \
  "$(cygpath -w "$ROOT/apps/desktop/main.py")"

echo "[6/6] Debug build finished; run the real GUI manually (close it to finish logging)"
echo ""
echo "Qt probe exit: $QT_RC; log: $DIST/qt-probe.log"
echo "Fault log: $DIST/python-faults.log"
echo "Debug EXE: $DIST/AICarScannerDebug/AICarScannerDebug.exe"
echo ""
echo "RUN THIS IN GIT BASH:"
echo "  export AI_CAR_BACKEND_URL=https://ai-car-scaner.onrender.com"
echo "  export AI_CAR_DISABLE_LLM_AUTOSTART=1"
echo "  export AI_CAR_DISABLE_NATIVE_TASKBAR_ICON=1"
echo "  export QT_DEBUG_PLUGINS=1"
echo "  export PYTHONFAULTHANDLER=1"
echo "  export AI_CAR_DEBUG_FAULT_LOG=\"$(cygpath -w "$ROOT/$DIST/python-faults.log")\""
echo "  ./$DIST/AICarScannerDebug/AICarScannerDebug.exe > $DIST/desktop-run.log 2>&1"
echo "  echo \"Exit code: \$?\""
echo "  tail -n 100 $DIST/desktop-run.log"
