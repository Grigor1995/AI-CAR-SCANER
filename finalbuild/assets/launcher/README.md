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
