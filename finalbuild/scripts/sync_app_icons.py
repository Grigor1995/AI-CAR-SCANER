"""Package the original transparent Desktop logo for all native launchers."""
from pathlib import Path
from shutil import copyfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ROOT / 'assets/AI-Car-Scanner-master.png'
    with Image.open(source) as original:
        logo = original.convert('RGBA')
    # Keep one canonical transparent logo, including the Desktop derivatives.
    for relative in ('assets/ai-car-scanner-icon.png', 'assets/launcher/mobile-app-icon.png',
                     'assets/AI-Car-Scanner-mobile.png'):
        copyfile(source, ROOT / relative)
    logo.save(ROOT / 'assets/AI-Car-Scanner.webp', lossless=True)
    logo.save(ROOT / 'assets/AI-Car-Scanner.ico', sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
    res = ROOT / 'apps/mobile-android/app/src/main/res'
    for density, size in [('mdpi',48), ('hdpi',72), ('xhdpi',96), ('xxhdpi',144), ('xxxhdpi',192), ('',192)]:
        folder = res / ('mipmap' + (f'-{density}' if density else ''))
        logo.resize((size,size), Image.Resampling.LANCZOS).save(folder / 'ic_launcher.webp', lossless=True)
    # Adaptive launchers mask the outer area: keep the complete mark in the safe zone.
    foreground = Image.new('RGBA', (432,432))
    mark = logo.resize((264,264), Image.Resampling.LANCZOS)
    foreground.alpha_composite(mark, (84,84))
    foreground.save(res / 'drawable-nodpi/ic_launcher_foreground.png')
    monochrome = Image.new('RGBA', foreground.size, 'white')
    monochrome.putalpha(foreground.getchannel('A'))
    monochrome.save(res / 'drawable-nodpi/ic_launcher_monochrome.png')
    # Apple requires an opaque App Store icon; preserve the same mark on black.
    ios = Image.new('RGB', (1024,1024), 'black')
    ios.paste(logo, (0,0), logo.getchannel('A'))
    ios.save(ROOT / 'apps/mobile-ios/AICarScanner/Assets.xcassets/AppIcon.appiconset/ai-car-scanner-icon.png')


if __name__ == '__main__':
    main()
