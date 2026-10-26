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

`mobile-app-icon.png` is generated neon-blue abstract vehicle app branding. Native
Android density/adaptive assets and the opaque iOS 1024 icon derive from this
master. Android themed icons use a separate monochrome vehicle vector.
