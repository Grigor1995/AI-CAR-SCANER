# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules

spec_path = Path(SPEC).resolve()
project_root = next(
    (parent for parent in spec_path.parents if (parent / "apps" / "desktop" / "backend_worker.py").is_file()),
    spec_path.parent,
)
backend_root = project_root / "backend"
# Uvicorn imports "api.main:app" dynamically. PyInstaller cannot discover
# modules behind the import string by analyzing backend_worker.py alone.
# Include the first-party backend packages in PYZ, not just as raw datas.
sys.path.insert(0, str(backend_root))
backend_packages = (
    "api", "diagnostic", "ai", "device", "acquisition", "telemetry",
    "vehicle", "vehicle_diagnostic", "multi_ecu", "network_discovery",
    "simulator", "professional_platform",
    "observability", "security",
)
backend_hiddenimports = ["api.main", "global_data"]
for package in backend_packages:
    backend_hiddenimports.extend(collect_submodules(package))

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
        "serial.tools.list_ports", "serial", "bleak",
        *backend_hiddenimports,
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="backend_service", console=True)
