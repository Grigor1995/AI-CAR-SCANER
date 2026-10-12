from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ANDROID_ICON = ROOT / "apps" / "mobile-android" / "app" / "src" / "main" / "res" / "mipmap" / "ic_launcher.webp"
DESKTOP_WEBP = ROOT / "assets" / "AI-Car-Scanner.webp"
DESKTOP_ICO = ROOT / "assets" / "AI-Car-Scanner.ico"


def main() -> None:
    if not ANDROID_ICON.is_file():
        raise FileNotFoundError(f"Android launcher icon not found: {ANDROID_ICON}")
    if not DESKTOP_WEBP.is_file():
        raise FileNotFoundError(f"Desktop icon source not found: {DESKTOP_WEBP}")

    with Image.open(ANDROID_ICON) as android_icon, Image.open(DESKTOP_WEBP) as desktop_copy:
        android_rgba = android_icon.convert("RGBA")
        desktop_rgba = desktop_copy.convert("RGBA")
        if android_rgba.size != desktop_rgba.size or android_rgba.tobytes() != desktop_rgba.tobytes():
            raise RuntimeError(
                "Android launcher icon and assets/AI-Car-Scanner.webp differ. "
                "Refusing to generate a mismatched Desktop icon."
            )
        android_rgba.save(
            DESKTOP_ICO,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    print(f"Generated Windows icon from Android launcher asset: {DESKTOP_ICO}")


if __name__ == "__main__":
    main()
