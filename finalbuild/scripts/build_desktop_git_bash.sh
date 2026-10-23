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
# PY is set after locating the user's existing Python 3.14 virtual environment.
ZIP=dist-release/AICarScanner-icon-preview.zip

echo "[1/8] Locate the existing Python 3.14 x64 Desktop virtual environment"
# Override in Git Bash when necessary:
#   export AI_CAR_DESKTOP_VENV="$HOME/Desktop/.venv"
# No Python installation or virtual environment creation takes place here.
VENV_CANDIDATES=()
if [[ -n "${AI_CAR_DESKTOP_VENV:-}" ]]; then
  VENV_CANDIDATES+=("$AI_CAR_DESKTOP_VENV")
else
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then VENV_CANDIDATES+=("$VIRTUAL_ENV"); fi
  VENV_CANDIDATES+=(
    "apps/desktop/.venv"
    "Desktop/.venv"
    ".venv"
    "../.venv"
    "$HOME/Desktop/.venv"
  )
fi

PY=""
for candidate in "${VENV_CANDIDATES[@]}"; do
  # Accept both Git Bash paths (/c/...) and Windows C:\... paths.
  candidate="$(cygpath -u "$candidate")"
  executable="$candidate/Scripts/python.exe"
  if [[ ! -f "$executable" ]]; then continue; fi
  if "$executable" -c 'import sys,struct; assert sys.platform=="win32" and sys.version_info[:2]==(3,14) and struct.calcsize("P")==8 and sys.prefix!=sys.base_prefix' >/dev/null 2>&1; then
    PY="$executable"
    break
  fi
  echo "[SKIP] Not a Python 3.14 x64 venv: $executable"
done
if [[ -z "$PY" ]]; then
  echo "[ERROR] Could not find an existing Windows Python 3.14 x64 .venv." >&2
  echo "Set its exact directory in Git Bash, then rerun:" >&2
  echo '  export AI_CAR_DESKTOP_VENV="$HOME/Desktop/.venv"' >&2
  echo "  bash scripts/build_desktop_git_bash.sh" >&2
  exit 2
fi
echo "Using existing venv Python: $PY"
"$PY" -c 'import sys; print("Version:",sys.version.split()[0]); print("Executable:",sys.executable); print("Environment:",sys.prefix)'

echo "[2/8] Ensure Desktop and backend dependencies in the existing venv"
"$PY" -m pip --version
"$PY" -m pip install -r requirements.txt -r apps/desktop/requirements-dev.txt

echo "[3/8] Run targeted regression tests before packaging"
# Keep default-port assertions reproducible even if the user has custom shell settings.
unset AI_CAR_BACKEND_URL AI_CAR_BACKEND_PORT LOCAL_LLM_SERVER_URL LOCAL_LLM_SERVER_PORT LOCAL_LLM_SERVER_HOST
export QT_QPA_PLATFORM=offscreen
"$PY" -m pytest -q apps/desktop/test_smoke.py   apps/desktop/tests/test_api_client.py   apps/desktop/tests/test_prepare_windows_icon_coverage.py apps/desktop/tests/test_stage_windows_icons.py   tests/desktop/test_phase32_ports_and_timeout.py   tests/desktop/test_phase25_standalone.py

echo "[4/8] Stage consistent icon formats without modifying tracked artwork"
# Keep the committed master for ordinary builds. If the Desktop PNG was edited
# locally, use that artwork instead of silently discarding it.
ICON_SOURCE="assets/AI-Car-Scanner-master.png"
if [[ -f assets/design-preview/ai-scanner-neon-car-icon.svg ]]; then
  "$PY" apps/desktop/neon_icon_build.py \
    --svg assets/design-preview/ai-scanner-neon-car-icon.svg \
    --output build-release/neon-icon-master.png
  ICON_SOURCE="build-release/neon-icon-master.png"
fi
if ! git diff --quiet HEAD -- assets/AI-Car-Scanner-mobile.png; then
  ICON_SOURCE="assets/AI-Car-Scanner-mobile.png"
  echo "[ICON] Locally edited Desktop PNG detected; using it as build source."
fi
STAGED_ICONS="build-release/icon-staged-assets"
"$PY" apps/desktop/stage_windows_icons.py \
  --source "$ICON_SOURCE" --output-dir "$STAGED_ICONS"
export AI_CAR_ICON_STAGE_DIR="$(cygpath -w "$ROOT/$STAGED_ICONS")"
export AI_CAR_VERIFY_ASSET_DIR="$AI_CAR_ICON_STAGE_DIR"

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
cp "$STAGED_ICONS"/AI-Car-Scanner-master.png "$STAGED_ICONS"/AI-Car-Scanner-mobile.png "$STAGED_ICONS"/AI-Car-Scanner.webp "$STAGED_ICONS"/AI-Car-Scanner.ico "$DIST/icons/"
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
