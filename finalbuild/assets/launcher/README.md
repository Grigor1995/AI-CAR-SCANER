# Desktop launch artwork

`background.png` is project-generated AI artwork: a dark automotive workshop,
blue sedan and circuit/engine graphics, created for this launch menu.

The twelve numbered SVG files are original vector UI images. Their names use
stable Desktop page IDs, independent of navigation order and interface language.
All assets are local and packaged by `AICarScanner.spec`; the launcher makes no
network requests for its artwork.

`icons-3d.png` is a project-generated transparent 4-column × 3-row sprite atlas
in the approved 3D Automotive style. Row-major IDs are
`11, 3, 2, 1, 4, 6, 8, 7, 9, 10, 0, 5`. The launcher extracts cells in memory;
labels are native, translated text. SVG files remain an offline fallback.

`brand-car.png` and the current `background.png` are generated abstract neon-blue
vehicle illustrations, without an identifiable real production model. The
Vehicles and Main menu **top-navigation** icons use `brand-car.png`, which
is byte-identical to Android/iOS `launcher_car.png`. All other navigation
icons use the same transparent 3D atlas: `icons-3d.png` is packaged as
`launcher_icons.png` on mobile. Page IDs differ between clients, so icons
are mapped by workflow purpose, not numeric ID. Main-menu **cards** show the
same 3D icons on Desktop, Android and iOS with translated text labels.
No manufacturer photo is used for branding.

The **installed app icon** is the silver/black D&A TOOL artwork in
`assets/AI-Car-Scanner-master.png` (1024x1024, opaque). The exact same PNG
is tracked in Desktop's `assets/AI-Car-Scanner-mobile.png`, Android's
`res/drawable-nodpi/ic_launcher_foreground.png`, and iOS's
`AppIcon.appiconset/ai-car-scanner-icon.png`. Android's adaptive icon uses an
18dp safe-area inset, and its Android-13 monochrome override is intentionally
omitted to prevent a different generic themed icon. The Windows executable
uses a multi-resolution ICO staged from the same master by the build scripts.
Use `python scripts/regenerate_native_icons.py` to refresh legacy mipmap
WEBP and tracked Desktop ICO/WEBP files from the master before release. The
previous neon-blue `mobile-app-icon.png` is retained only as an archival
concept, **not** as the installed application icon.
