# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import subprocess
import sys

spec_path = Path(SPEC).resolve()
project_root = next(
    (parent for parent in spec_path.parents if (parent / "apps" / "desktop" / "main.py").is_file()),
    spec_path.parent,
)
# Rebuild the Windows icon from the dedicated Desktop master asset.
subprocess.run(
    [sys.executable, str(project_root / "apps" / "desktop" / "prepare_windows_icon.py")],
    cwd=str(project_root),
    check=True,
)
# Optional llama-server is a separately managed runtime dependency. Never
# embed an arbitrary PATH executable in the GUI: it is packaged separately
# by the standalone release script when explicitly available.
binaries = []
icon_file = project_root / "assets" / "AI-Car-Scanner.ico"
if not icon_file.is_file():
    raise FileNotFoundError(f"Required application icon not found: {icon_file}")

a = Analysis(
    [str(project_root / "apps" / "desktop" / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=[(str(project_root / "assets" / "AI-Car-Scanner.ico"), "assets"),
           (str(project_root / "assets" / "AI-Car-Scanner.webp"), "assets"),
           (str(project_root / "assets" / "AI-Car-Scanner-mobile.png"), "assets"),
           (str(project_root / "shared" / "vehicle_catalog.json"), "shared"),
          ],
    hiddenimports=[
        "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
        "requests", "apps.desktop.ui", "apps.desktop.api_client",
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="AICarScanner", console=False, icon=str(icon_file))
