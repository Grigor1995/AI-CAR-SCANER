# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

spec_path = Path(SPEC).resolve()
project_root = next(
    (parent for parent in spec_path.parents if (parent / "apps" / "desktop" / "main.py").is_file()),
    spec_path.parent,
)
# Consume existing artwork only. Never regenerate/overwrite tracked icons
# from inside PyInstaller (especially important for uncommitted local artwork).
# Git Bash builds set AI_CAR_ICON_STAGE_DIR to isolated build-release assets.
asset_root = Path(os.environ.get("AI_CAR_ICON_STAGE_DIR") or (project_root / "assets")).resolve()
for filename in ("AI-Car-Scanner-mobile.png", "AI-Car-Scanner.webp", "AI-Car-Scanner.ico"):
    if not (asset_root / filename).is_file():
        raise FileNotFoundError(f"Required Desktop icon missing: {asset_root / filename}")
# Optional llama-server is a separately managed runtime dependency. Never
# embed an arbitrary PATH executable in the GUI: it is packaged separately
# by the standalone release script when explicitly available.
binaries = []
icon_file = asset_root / "AI-Car-Scanner.ico"
if not icon_file.is_file():
    raise FileNotFoundError(f"Required application icon not found: {icon_file}")

a = Analysis(
    [str(project_root / "apps" / "desktop" / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=[(str(asset_root / "AI-Car-Scanner.ico"), "assets"),
           (str(asset_root / "AI-Car-Scanner.webp"), "assets"),
           (str(asset_root / "AI-Car-Scanner-mobile.png"), "assets"),
           (str(project_root / "shared" / "vehicle_catalog.json"), "shared"),
           (str(project_root / "assets" / "vehicle_models"), "assets/vehicle_models"),
           (str(project_root / "assets" / "launcher"), "assets/launcher"),
          ],
    hiddenimports=[
        "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtSvg",
        "PySide6.QtPrintSupport", "PySide6.QtNetwork", "requests", "apps.desktop.ui",
        "apps.desktop.api_client", "apps.desktop.vehicle_artwork",
        "apps.desktop.demo_ui", "apps.desktop.backend_recovery",
    ],
    hookspath=[], hooksconfig={},
    # User-verified workaround: load PySide6.QtCore before PyInstaller's
    # cryptography/Qt runtime hooks on Windows Python 3.14 frozen GUI startup.
    runtime_hooks=[str(project_root / "apps" / "desktop" / "qt_early_runtime_hook.py")],
    excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="AICarScanner", console=False, icon=str(icon_file))
