# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(SPEC).resolve().parents[2]
backend_root = project_root / "backend"

a = Analysis(
    [str(project_root / "apps" / "desktop" / "backend_worker.py")],
    pathex=[str(project_root), str(backend_root)],
    binaries=[],
    datas=[(str(backend_root), "backend")],
    hiddenimports=[
        "uvicorn", "uvicorn.logging", "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets.auto",
        "api.device_routes", "serial.tools.list_ports", "serial", "bleak",
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="backend_service", console=True)
