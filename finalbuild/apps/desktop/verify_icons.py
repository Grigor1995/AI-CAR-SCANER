"""Verify the assets and native icon of a PyInstaller Desktop preview build.

Run `python apps/desktop/verify_icons.py` from finalbuild; the Windows
builder also sets AI_CAR_VERIFY_EXE_PATH to inspect the built EXE resource.
This checks icons only, without starting the backend, LLM or full GUI.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops
from PySide6.QtGui import QGuiApplication, QIcon


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def _embedded_icon_count() -> int | None:
    exe_path = os.environ.get("AI_CAR_VERIFY_EXE_PATH")
    if sys.platform != "win32" or not (exe_path or getattr(sys, "frozen", False)):
        return None
    from ctypes import wintypes

    extract = ctypes.windll.shell32.ExtractIconExW
    extract.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_int,
        ctypes.POINTER(wintypes.HICON),
        ctypes.POINTER(wintypes.HICON),
        wintypes.UINT,
    ]
    extract.restype = wintypes.UINT
    target = Path(exe_path).resolve() if exe_path else Path(sys.executable).resolve()
    if not target.is_file():
        raise FileNotFoundError(f"Windows executable does not exist: {target}")
    return int(extract(str(target), -1, None, None, 0))


def verify_icons() -> int:
    """Return 0 only when the bundled images, Qt icon, and EXE icon verify."""
    # Git Bash preview builds verify staged assets so a user-edited PNG can
    # be packaged without rewriting the tracked PNG/WEBP/ICO source files.
    staged = os.environ.get("AI_CAR_VERIFY_ASSET_DIR")
    assets = Path(staged).expanduser() if staged else _resource_root() / "assets"
    filenames = (
        "AI-Car-Scanner-mobile.png",
        "AI-Car-Scanner.webp",
        "AI-Car-Scanner.ico",
    )
    report: dict[str, object] = {
        "status": "FAIL",
        "mode": "packaged" if getattr(sys, "frozen", False) else "source",
        "checks": {},
        "errors": [],
    }
    checks: dict[str, object] = report["checks"]  # type: ignore[assignment]
    errors: list[str] = report["errors"]  # type: ignore[assignment]

    try:
        for filename in filenames:
            path = assets / filename
            if not path.is_file():
                raise FileNotFoundError(f"Required bundled icon is missing: {path}")
            with Image.open(path) as icon:
                icon.verify()
            checks[filename] = {
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }

        png_path = assets / filenames[0]
        webp_path = assets / filenames[1]
        ico_path = assets / filenames[2]
        with Image.open(png_path) as png, Image.open(webp_path) as webp:
            if png.width < 256 or png.height < 256:
                raise ValueError("PNG launcher icon is smaller than 256 pixels")
            foreground = png.convert("RGBA")
            comparison = webp.convert("RGBA")
            if foreground.size != comparison.size:
                raise ValueError("PNG and WEBP Desktop icon dimensions differ")
            if ImageChops.difference(
                foreground.getchannel("A"), comparison.getchannel("A")
            ).getbbox():
                raise ValueError("PNG and WEBP Desktop icon alpha channels differ")
            # WEBP codecs may normalize invisible RGB values below fully
            # transparent pixels. Compare the visible icon on both black
            # and white backgrounds instead of rejecting invisible RGB data.
            for background in ((0, 0, 0, 255), (255, 255, 255, 255)):
                base = Image.new("RGBA", foreground.size, background)
                a = Image.alpha_composite(base, foreground).convert("RGB")
                b = Image.alpha_composite(base, comparison).convert("RGB")
                maximum = max(hi for _lo, hi in ImageChops.difference(a, b).getextrema())
                if maximum > 1:
                    raise ValueError("PNG and WEBP Desktop icons differ visually")
            checks["png_webp_parity"] = True

        with Image.open(ico_path) as ico:
            if ico.format != "ICO" or (256, 256) not in ico.ico.sizes():
                raise ValueError("Windows ICO does not contain a 256x256 frame")
            checks["ico_sizes"] = sorted([list(size) for size in ico.ico.sizes()])

        app = QGuiApplication.instance() or QGuiApplication([])
        qt_icon = QIcon(str(png_path))
        if qt_icon.isNull() or qt_icon.pixmap(64, 64).isNull():
            raise RuntimeError("Qt could not decode the Desktop window icon PNG")
        checks["qt_window_icon"] = True
        # Retain the QApplication lifetime through the Qt check.
        del app

        exe_icons = _embedded_icon_count()
        if exe_icons is not None:
            if exe_icons < 1:
                raise RuntimeError("Packaged Windows executable has no native icon")
            checks["embedded_exe_icon_count"] = exe_icons

    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    report["status"] = "PASS" if not errors else "FAIL"
    destination = Path(
        os.environ.get("AI_CAR_ICON_REPORT_PATH", "desktop-icon-report.json")
    ).expanduser()
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        errors.append(f"Unable to write icon report: {exc}")
        report["status"] = "FAIL"

    if sys.stdout is not None:
        print(f"Desktop icon verification: {report['status']}")
        if errors:
            print("; ".join(errors), file=sys.stderr)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(verify_icons())
