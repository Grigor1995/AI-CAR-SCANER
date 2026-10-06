# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from shutil import which

project_root = Path(SPEC).resolve().parents[2]
server = which("llama-server.exe")
binaries = [(server, ".")] if server else []
icon_file = project_root / "assets" / "AI-Car-Scanner.ico"

a = Analysis(
    [str(project_root / "apps" / "desktop" / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=[(str(project_root / "assets" / "AI-Car-Scanner.ico"), "assets"),
           (str(project_root / "assets" / "ai-car-scanner-icon.png"), "assets")],
    hiddenimports=[
        "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
        "requests", "apps.desktop.ui", "apps.desktop.api_client",
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="AICarScanner", console=False, icon=str(icon_file) if icon_file.is_file() else None)
