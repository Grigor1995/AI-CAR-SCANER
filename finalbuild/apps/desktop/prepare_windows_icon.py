from __future__ import annotations

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ANDROID_ICON = ROOT / "apps" / "mobile-android" / "app" / "src" / "main" / "res" / "mipmap" / "ic_launcher.webp"
DEFAULT_ANDROID_ICON = ANDROID_ICON
DESKTOP_MASTER = ROOT / "assets" / "AI-Car-Scanner-master.png"
DESKTOP_WEBP = ROOT / "assets" / "AI-Car-Scanner.webp"
DESKTOP_PNG = ROOT / "assets" / "AI-Car-Scanner-mobile.png"
DESKTOP_ICO = ROOT / "assets" / "AI-Car-Scanner.ico"
ICON_SIZES = [(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]


def main() -> None:
    # Preserve historical Android-based behavior in isolated test environments
    # and when the dedicated Desktop master is unavailable.
    source = DESKTOP_MASTER if ANDROID_ICON == DEFAULT_ANDROID_ICON and DESKTOP_MASTER.is_file() else ANDROID_ICON
    if not source.is_file():
        raise FileNotFoundError(f"Android launcher icon not found: {ANDROID_ICON}")

    with Image.open(source) as original:
        icon = original.convert("RGBA")
        if icon.width < 256 or icon.height < 256:
            icon = icon.resize((512,512), Image.Resampling.LANCZOS)

        DESKTOP_WEBP.parent.mkdir(parents=True, exist_ok=True)
        icon.save(DESKTOP_WEBP, format="WEBP", lossless=True, quality=100, method=6)
        icon.save(DESKTOP_PNG, format="PNG", optimize=True)
        icon.save(DESKTOP_ICO, format="ICO", sizes=ICON_SIZES)

    for output in (DESKTOP_WEBP, DESKTOP_PNG, DESKTOP_ICO):
        if not output.is_file() or output.stat().st_size < 128:
            raise RuntimeError(f"Generated Desktop icon is missing or invalid: {output}")
    with Image.open(DESKTOP_ICO) as check:
        if check.format != "ICO" or check.width < 16 or check.height < 16:
            raise RuntimeError(f"Generated Windows icon failed validation: {DESKTOP_ICO}")
    print(f"Generated Desktop PNG, WEBP, and Windows ICO from {source}: {DESKTOP_ICO}")


if __name__ == "__main__":
    main()
