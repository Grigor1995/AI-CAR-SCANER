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
# Uvicorn's string-based "api.main:app" dynamic import is invisible to
# PyInstaller's static graph. Bundle real Python bytecode for our routers and
# domain modules, not merely their .py source in Analysis.datas.
sys.path.insert(0, str(backend_root))
api_packages = (
    "api", "diagnostic", "ai", "device", "acquisition",
    "telemetry", "vehicle", "vehicle_diagnostic", "multi_ecu",
    "multi_bus", "network_discovery", "simulator",
    "professional_platform", "security", "observability",
)
api_hiddenimports = ["api.main", "global_data", "backend.scripts.seed_vehicle_catalog"]
for package in api_packages:
    api_hiddenimports.extend(collect_submodules(package))

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
        "diagnostic.local_database", *api_hiddenimports,
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="backend_service", console=True)
