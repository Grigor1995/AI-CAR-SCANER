# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

spec_path = Path(SPEC).resolve()
project_root = next(
    (parent for parent in spec_path.parents if (parent / "apps" / "desktop" / "backend_worker.py").is_file()),
    spec_path.parent,
)
backend_root = project_root / "backend"

a = Analysis(
    [str(project_root / "apps" / "desktop" / "backend_worker.py")],
    pathex=[str(project_root), str(backend_root)],
    binaries=[],
    datas=[(str(backend_root), "backend"),
           (str(project_root / "data" / "vehicle_fitment_catalog.json"), "data")],
    hiddenimports=[
        "uvicorn", "uvicorn.logging", "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets.auto",
        "api.device_routes", "serial.tools.list_ports", "serial", "bleak",
        "diagnostic.local_database", "backend.scripts.seed_vehicle_catalog",
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="backend_service", console=True)
