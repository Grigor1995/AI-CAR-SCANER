"""Synchronize installed Desktop, Android and iOS icons from one D&A TOOL master.

Run once before making a release:
    python scripts/regenerate_native_icons.py

The source is assets/AI-Car-Scanner-master.png, a 1024px opaque image.
This command intentionally updates generated, tracked application icon files.
It never modifies the 3D Main menu sprite atlas or launcher-car illustrations.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets" / "AI-Car-Scanner-master.png"
DESKTOP_PNG = ROOT / "assets" / "AI-Car-Scanner-mobile.png"
DESKTOP_WEBP = ROOT / "assets" / "AI-Car-Scanner.webp"
DESKTOP_ICO = ROOT / "assets" / "AI-Car-Scanner.ico"
ANDROID_RES = ROOT / "apps" / "mobile-android" / "app" / "src" / "main" / "res"
ANDROID_FOREGROUND = ANDROID_RES / "drawable-nodpi" / "ic_launcher_foreground.png"
IOS_APPICON = ROOT / "apps" / "mobile-ios" / "AICarScanner" / "Assets.xcassets" / "AppIcon.appiconset" / "ai-car-scanner-icon.png"
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def regenerate() -> None:
    with Image.open(MASTER) as original:
        original.load()
        if original.size != (1024, 1024) or original.mode != "RGB":
            raise ValueError("Canonical iOS-compatible master must be opaque RGB 1024x1024")
        icon = original.copy()

    # Copy source bytes, preserving exact cross-platform binary equality.
    for destination in (DESKTOP_PNG, ANDROID_FOREGROUND, IOS_APPICON):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MASTER, destination)
    DESKTOP_WEBP.parent.mkdir(parents=True, exist_ok=True)
    icon.save(DESKTOP_WEBP, "WEBP", lossless=True, quality=100, method=6)
    icon.save(DESKTOP_ICO, "ICO", sizes=ICO_SIZES)

    # Android minimum SDK is 26: modern devices use the v26 adaptive icon.
    # Generate density-specific fallback icons too, for launchers that ask for
    # older raster resources. These are not the adaptive foreground.
    for density, size in DENSITIES.items():
        path = ANDROID_RES / f"mipmap-{density}" / "ic_launcher.webp"
        path.parent.mkdir(parents=True, exist_ok=True)
        icon.resize((size, size), Image.Resampling.LANCZOS).save(
            path, "WEBP", lossless=True, quality=100, method=6
        )
    icon.resize((512, 512), Image.Resampling.LANCZOS).save(
        ANDROID_RES / "mipmap" / "ic_launcher.webp",
        "WEBP", lossless=True, quality=100, method=6
    )
    print("Synced Desktop ICO/WEBP/PNG, Android adaptive+density icons and iOS app icon from", MASTER)


def check() -> None:
    source_bytes = MASTER.read_bytes()
    for path in (DESKTOP_PNG, ANDROID_FOREGROUND, IOS_APPICON):
        if path.read_bytes() != source_bytes:
            raise ValueError(f"App icon is not byte-identical to Desktop master: {path}")
    with Image.open(MASTER) as im:
        if im.size != (1024, 1024) or im.mode != "RGB":
            raise ValueError("Expected opaque 1024x1024 RGB Desktop master")
    print("Native Desktop/Android/iOS app icon source bytes are identical")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Only validate canonical installed app PNGs")
    args = parser.parse_args()
    if not args.check:
        regenerate()
    check()


if __name__ == "__main__":
    main()
