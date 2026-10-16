#!/usr/bin/env bash
# Git Bash Windows x64 builder; run from finalbuild with:
# bash scripts/build_desktop_git_bash.sh
set -Eeuo pipefail
trap 'status=$?; echo "[FAIL] Build stopped at line $LINENO (exit $status)" >&2' ERR

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) echo "[ERROR] This build requires Git Bash on Windows x64." >&2; exit 2 ;;
esac

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
DIST=dist-release/icon-preview
WORK=build-release/icon-preview
PY=build-release/venv-icon-preview/Scripts/python.exe
ZIP=dist-release/AICarScanner-icon-preview.zip

echo "[1/8] Check Windows Python 3.13 x64"
if command -v py >/dev/null 2>&1 && py -3.13 -c "import sys; assert sys.version_info[:2]==(3,13)" >/dev/null 2>&1; then
  py -3.13 -c 'import sys,struct; assert sys.platform=="win32" and struct.calcsize("P")==8'
  mkdir -p build-release
  if [[ ! -f "$PY" ]]; then py -3.13 -m venv build-release/venv-icon-preview; fi
elif command -v python >/dev/null 2>&1 && python -c "import sys; assert sys.version_info[:2]==(3,13)" >/dev/null 2>&1; then
  python -c 'import sys,struct; assert sys.platform=="win32" and struct.calcsize("P")==8'
  mkdir -p build-release
  if [[ ! -f "$PY" ]]; then python -m venv build-release/venv-icon-preview; fi
else
  echo "[ERROR] Install Windows Python 3.13 x64, verify with: py -3.13 --version" >&2
  exit 2
fi
"$PY" -c 'import sys,struct; assert sys.platform=="win32" and sys.version_info[:2]==(3,13) and struct.calcsize("P")==8, "Stale or incorrect venv"'

echo "[2/8] Install Desktop and backend requirements"
"$PY" -m pip install --upgrade pip setuptools wheel
"$PY" -m pip install -r requirements.txt -r apps/desktop/requirements-dev.txt

echo "[3/8] Run targeted regression tests before packaging"
export QT_QPA_PLATFORM=offscreen
"$PY" -m pytest -q apps/desktop/test_smoke.py   apps/desktop/tests/test_api_client.py   apps/desktop/tests/test_prepare_windows_icon_coverage.py   tests/desktop/test_phase32_ports_and_timeout.py   tests/desktop/test_phase25_standalone.py

echo "[4/8] Check unsaved generated icons before regeneration"
for asset in assets/AI-Car-Scanner-mobile.png assets/AI-Car-Scanner.webp assets/AI-Car-Scanner.ico; do
  if ! git diff --quiet HEAD -- "$asset"; then
    echo "[ERROR] Uncommitted changes would be overwritten in $asset" >&2
    echo "Preserve or commit the modified icon first. No files were removed." >&2
    exit 3
  fi
done
"$PY" apps/desktop/prepare_windows_icon.py

echo "[5/8] Create an isolated PyInstaller build (do not touch dist/)"
mkdir -p dist-release build-release
rm -rf -- "$DIST" "$WORK"
mkdir -p "$DIST" "$WORK"
"$PY" -m PyInstaller --noconfirm --clean   --distpath "$DIST" --workpath "$WORK/backend"   apps/desktop/specs/backend_service.spec
"$PY" -m PyInstaller --noconfirm --clean   --distpath "$DIST" --workpath "$WORK/desktop"   apps/desktop/specs/AICarScanner.spec

for artifact in "$DIST/AICarScanner.exe" "$DIST/backend_service.exe"; do
  [[ -s "$artifact" ]] || { echo "[ERROR] Missing executable: $artifact" >&2; exit 4; }
done

echo "[6/8] Validate generated icons, Qt preview and EXE icon resource"
mkdir -p "$DIST/icons"
cp assets/AI-Car-Scanner-master.png assets/AI-Car-Scanner-mobile.png   assets/AI-Car-Scanner.webp assets/AI-Car-Scanner.ico "$DIST/icons/"
export AI_CAR_VERIFY_EXE_PATH="$(cygpath -w "$ROOT/$DIST/AICarScanner.exe")"
export AI_CAR_ICON_REPORT_PATH="$(cygpath -w "$ROOT/$DIST/desktop-icon-report.json")"
"$PY" apps/desktop/verify_icons.py
"$PY" -c 'import json,os,pathlib; r=json.loads(pathlib.Path(os.environ["AI_CAR_ICON_REPORT_PATH"]).read_text(encoding="utf-8")); assert r["status"]=="PASS", r; print("Icon verification:",r["status"])'
unset AI_CAR_VERIFY_EXE_PATH AI_CAR_ICON_REPORT_PATH

echo "[7/8] Create distribution archive"
cat > "$DIST/README_GIT_BASH.txt" <<'TXT'
Extract the entire ZIP; keep the two .exe files next to each other.
To start the GUI in Git Bash, from the extracted folder:
  export AI_CAR_BACKEND_URL=https://ai-car-scaner.onrender.com
  export AI_CAR_DISABLE_LLM_AUTOSTART=1
  ./AICarScanner.exe
Inspect Explorer/taskbar/window icons and test diagnostic flow.
The icon check does not prove the complete GUI runs successfully.
The GGUF AI model and llama-server are not bundled.
TXT

"$PY" - "$DIST" "$ZIP" <<'PYCODE'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import sys
src, dest = Path(sys.argv[1]), Path(sys.argv[2])
with ZipFile(dest, "w", compression=ZIP_DEFLATED) as out:
    for path in sorted(src.rglob("*")):
        if path.is_file():
            out.write(path, path.relative_to(src))
print(f"ZIP ready: {dest} ({dest.stat().st_size:,} bytes)")
PYCODE

echo "[8/8] Source and icon checks completed; packaged GUI must be launched separately"
echo "[PASS] Created: $DIST/AICarScanner.exe"
echo "[PASS] Created: $DIST/backend_service.exe"
echo "[PASS] Created: $DIST/desktop-icon-report.json"
echo "[PASS] Created: $ZIP"
