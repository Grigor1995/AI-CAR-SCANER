"""Technical exports of approved generated originals; no visual recoloring.

Desktop retains alpha. Android adaptive foreground uses the central safe zone.
iOS requires an opaque 1024px asset. Original generated PNGs are never mutated.
"""
from pathlib import Path
import json
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ROLES = ('user', 'customer', 'market')
DENSITIES = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}

def export(root=ROOT):
    for role in ROLES:
        folder = root/'assets/app_icons'/role
        with Image.open(folder/'source.png') as source:
            image = source.convert('RGBA')
        image = ImageOps.contain(image, (1024, 1024), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (1024, 1024))
        canvas.alpha_composite(image, ((1024-image.width)//2, (1024-image.height)//2))
        canvas.save(folder/'icon.png')
        canvas.save(folder/'icon.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
        android = root/'apps/mobile-android/app/src'/role/'res'
        for density, factor in DENSITIES.items():
            mipmap = android/f'mipmap-{density}'; mipmap.mkdir(parents=True, exist_ok=True)
            canvas.resize((int(48*factor),)*2, Image.Resampling.LANCZOS).save(mipmap/'ic_launcher.webp', lossless=True)
            drawable = android/f'drawable-{density}'; drawable.mkdir(parents=True, exist_ok=True)
            safe = Image.new('RGBA', (int(108*factor),)*2)
            glyph = canvas.resize((int(66*factor),)*2, Image.Resampling.LANCZOS)
            safe.alpha_composite(glyph, ((safe.width-glyph.width)//2,)*2)
            safe.save(drawable/'product_launcher_foreground.png')
        adaptive=android/'mipmap-anydpi-v26'; adaptive.mkdir(parents=True, exist_ok=True)
        (adaptive/'ic_launcher.xml').write_text('''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/product_launcher_background" />
    <foreground android:drawable="@drawable/product_launcher_foreground" />
</adaptive-icon>\n''')
        values=android/'values'; values.mkdir(exist_ok=True)
        (values/'icon_colors.xml').write_text('<resources><color name="product_launcher_background">#061222</color></resources>\n')
        ios = root/'apps/mobile-ios/AICarScanner/Assets.xcassets'/f'AppIcon{role.title()}.appiconset'
        ios.mkdir(parents=True, exist_ok=True)
        opaque = Image.new('RGBA', canvas.size, '#061222'); opaque.alpha_composite(canvas)
        opaque.convert('RGB').save(ios/'icon.png')
        (ios/'Contents.json').write_text(json.dumps({'images':[{'filename':'icon.png', 'idiom':'universal', 'platform':'ios','size':'1024x1024'}],
                                                   'info':{'author':'xcode','version':1}}, indent=2)+'\n')

if __name__ == '__main__': export()
