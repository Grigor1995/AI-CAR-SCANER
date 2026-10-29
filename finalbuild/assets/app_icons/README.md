# Product app icons

Three original images generated specifically for USER, CUSTOMER and MARKET in
this change. Neon blue / silver automotive style, transparent originals, no text
or manufacturer logo. Existing shared application artwork remains unchanged.

- USER: vehicle/driver shield and steering wheel.
- CUSTOMER: vehicle inspection, wrench and diagnostic pulse.
- MARKET: automotive storefront, gear and spare part package.

`source.png` files are the unmodified generated originals. `icon.png`/`icon.ico`
and platform assets are technical size/format exports. Regenerate from finalbuild:
`python scripts/export_product_icons.py`. Desktop retains alpha; Android adaptive
foreground is sized within the safe zone; iOS AppIcon is flattened to the standard
dark background because iOS requires an opaque 1024px image.

Desktop role entry points and packaging choose the matching PNG/ICO. Android
role source sets override the launcher resources; iOS project.yml chooses the
matching AppIcon asset set per target. Source installer shortcuts use product ICOs.
