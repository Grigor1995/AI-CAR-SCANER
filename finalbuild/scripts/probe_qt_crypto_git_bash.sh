#!/usr/bin/env bash
# Isolate whether cryptography's PyInstaller runtime hook breaks Qt startup.
# This does not modify the existing Python 3.14 venv or Desktop executables.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
DIST=dist-debug
WORK=build-debug
CANDIDATES=()
if [[ -n "${AI_CAR_DESKTOP_VENV:-}" ]]; then
  CANDIDATES+=("$AI_CAR_DESKTOP_VENV")
else
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then CANDIDATES+=("$VIRTUAL_ENV"); fi
  CANDIDATES+=("apps/desktop/.venv" "Desktop/.venv" ".venv" "../.venv" "$HOME/Desktop/.venv")
fi
PY=""
for venv in "${CANDIDATES[@]}"; do
  candidate="$(cygpath -u "$venv")/Scripts/python.exe"
  if [[ -f "$candidate" ]] && "$candidate" -c 'import sys; assert sys.version_info[:2]==(3,14)' >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
if [[ -z "$PY" ]]; then echo "[ERROR] Python 3.14 venv not found" >&2; exit 2; fi
if ! "$PY" -c 'import cryptography,PyInstaller,PySide6'; then
  echo "[ERROR] Missing an expected package in the existing venv" >&2
  exit 3
fi
mkdir -p "$DIST" "$WORK"
unset QT_QPA_PLATFORM QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH QT_QPA_FONTDIR
export AI_CAR_EARLY_QTCORE=0
export PYTHONFAULTHANDLER=1
export AI_CAR_DEBUG_FAULT_LOG="$(cygpath -w "$ROOT/$DIST/crypto-probe-faults.log")"
echo "[ISOLATION] Build minimal Qt probe plus cryptography (no application UI/backend imports)."
"$PY" -m PyInstaller --noconfirm --clean --onedir --console --debug bootloader \
  --name AIQtCryptoProbe \
  --distpath "$DIST" --workpath "$WORK/qt-crypto" --specpath "$WORK" \
  --paths "$(cygpath -w "$ROOT")" \
  --runtime-hook "$(cygpath -w "$ROOT/apps/desktop/debug_runtime_hook.py")" \
  --hidden-import cryptography.hazmat.bindings._rust \
  --add-data "$(cygpath -w "$ROOT/assets/AI-Car-Scanner-mobile.png");assets" \
  "$(cygpath -w "$ROOT/apps/desktop/qt_freeze_probe.py")"
echo "[ISOLATION] Execute probe; it auto-closes when successful."
set +e
"$DIST/AIQtCryptoProbe/AIQtCryptoProbe.exe" > "$DIST/qt-crypto-probe.log" 2>&1
rc=$?
set -e
echo "[ISOLATION] Crypto Qt probe exit status: $rc"
grep -E '\[QT-PROBE\]|pyi_rth_|access violation|Fatal|ERROR' "$DIST/qt-crypto-probe.log" | tail -n 55 || true
if [[ -s "$DIST/crypto-probe-faults.log" ]]; then
  tail -n 30 "$DIST/crypto-probe-faults.log"
fi
if [[ "$rc" -eq 0 ]]; then
  echo "[RESULT] Crypto Qt probe passed. The Desktop bundle has an additional trigger."
else
  echo "[RESULT] Crypto Qt probe failed, suggesting a conflict related to the cryptography hook or its native dependencies."
fi
echo "[NOTE] Neither outcome by itself proves the identity of the failing DLL."
