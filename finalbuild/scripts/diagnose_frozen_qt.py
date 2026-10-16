"""Compare Qt/PySide6 native bundles after a Windows frozen startup crash.

Run from finalbuild/: python scripts/diagnose_frozen_qt.py
This script is read-only except for writing its JSON report in dist-debug/.
It deliberately does not import Qt or load any native DLL.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist-debug"
NAMES = ("AIQtProbe", "AICarScannerDebug")
KEYS = (
    "qt6", "pyside6", "shiboken6", "libcrypto", "libssl",
    "vcruntime", "msvcp", "icu", "zlib",
)


def is_native_candidate(p: Path) -> bool:
    name = p.name.lower()
    return p.suffix.lower() in {".pyd", ".dll"} and any(
        key in name for key in KEYS
    )


def scan(name: str) -> dict:
    internal = DIST / name / "_internal"
    result = {"folder": str(internal), "present": internal.is_dir(), "dlls": {}}
    if not internal.is_dir():
        return result
    for file in sorted(internal.rglob("*")):
        if not file.is_file() or not is_native_candidate(file):
            continue
        rel = file.relative_to(internal).as_posix()
        result["dlls"][rel] = {
            "name": file.name,
            "bytes": file.stat().st_size,
            "sha256": sha256(file.read_bytes()).hexdigest(),
        }
    return result


def main() -> int:
    print("Python executable:", sys.executable)
    packages = [
        "PySide6", "PySide6_Essentials", "PySide6_Addons",
        "shiboken6", "pyinstaller", "pyinstaller-hooks-contrib",
    ]
    versions = {}
    for package in packages:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "NOT INSTALLED"
    print("Package versions:", versions)
    print("QT_API:", os.environ.get("QT_API", "(unset)"))
    print("PATH:", os.environ.get("PATH", "")[:500])
    bundles = {name: scan(name) for name in NAMES}
    for name, result in bundles.items():
        print(f"Bundle {name}: present={result['present']} native files={len(result['dlls'])}")
    qt, app = (bundles[name]["dlls"] for name in NAMES)
    qt_by_filename = defaultdict(list)
    app_by_filename = defaultdict(list)
    for rel, data in qt.items():
        qt_by_filename[data["name"].lower()].append((rel, data))
    for rel, data in app.items():
        app_by_filename[data["name"].lower()].append((rel, data))
    names = sorted(set(qt_by_filename) | set(app_by_filename))
    differences = []
    for basename in names:
        q = qt_by_filename.get(basename, [])
        a = app_by_filename.get(basename, [])
        q_hashes = {item[1]["sha256"] for item in q}
        a_hashes = {item[1]["sha256"] for item in a}
        if q_hashes != a_hashes or len(q) != len(a):
            differences.append({
                "filename": basename,
                "qt_probe": [{"path": p, "sha256": d["sha256"]} for p, d in q],
                "desktop": [{"path": p, "sha256": d["sha256"]} for p, d in a],
            })
    report = {
        "venv_python": sys.executable,
        "versions": versions,
        "bundles": bundles,
        "differing_native_files": differences,
    }
    DIST.mkdir(parents=True, exist_ok=True)
    report_path = DIST / "qt-bundle-audit.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nDifferent/missing Qt-related DLL/PYD files:")
    for item in differences:
        print(" ", item["filename"])
        for name in NAMES:
            records = item["qt_probe" if name == NAMES[0] else "desktop"]
            for record in records:
                print(f"    {name}: {record['path']} sha256={record['sha256'][:16]}")
        if not item["qt_probe"] or not item["desktop"]:
            print("    [MISSING FROM ONE BUNDLE]")
    print("Report:", report_path)
    print("Differences are diagnostic clues, not proof of a specific DLL conflict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
