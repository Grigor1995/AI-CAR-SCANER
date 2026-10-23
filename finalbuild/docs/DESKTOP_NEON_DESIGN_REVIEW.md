# Neon 3D Desktop design — review branch

Branch: `design/neon-3d-ui-review-20261023`. Do **not** merge until manually reviewed on Windows.

## Scope
- Header Settings shortcut removed. Settings remains in **Application → Settings**.
- Dark desktop shell uses the existing locally packaged `assets/launcher/background.png` at low opacity, under a readable glass/navy overlay.
- Dashboard and Vehicles screens use the selected make/model/chassis **actual portrait** with neon-studio frame, keeping the image content intact.
- All QGroupBoxes, navigation controls and progress bars use layered gradients and cyan borders in dark mode. Light theme remains supported.
- Live Data and Dashboard channel trace charts render neon glow and subtle fills. Analog gauges gain halo and digital readouts but keep existing telemetry and band logic.
- Simulator parameter controls have synchronized horizontal sliders alongside numeric inputs. Real adapter acquisition controls are unchanged.
- Brand-neutral generic sedan SVG is now the preferred Qt application icon. Windows preview builders render that SVG to PNG, WEBP and ICO in isolated build directories; original tracked icons are not overwritten. **No BMW photo or logo is included in the new vector master.**
- Header/page icons remain compact and use the existing 3D launcher atlas.

## Git Bash — source preview
```bash
cd ~/Desktop/AI-CAR-SCANER/git/finalbuild
git fetch origin
git switch design/neon-3d-ui-review-20261023
python -m pytest -q apps/desktop/tests/test_neon_ui_design.py
python -m apps.desktop.main
```

## Windows icon preview build
```bash
export AI_CAR_DESKTOP_VENV="$HOME/Desktop/.venv"
bash scripts/build_desktop_git_bash.sh
```
Expect `dist-release/icon-preview/AICarScanner.exe`; inspect `dist-release/icon-preview/desktop-icon-report.json`.

## Validation required
1. Dashboard light/dark theme and viewport resizing, 3D cards and selected vehicle photo.
2. Live Data analog and chart modes, slider-to-numeric synchronization, metric/US units, backend acquisition.
3. Vehicle dialog/catalog unaffected by visual changes.
4. Native window, taskbar and EXE icons plus Windows PyInstaller smoke run.
5. Desktop regression, negative and performance checks. Do not mark them passing without local execution.

The 3D style here is a native Qt layered/lighting treatment, **not a realtime 3D engine or 3D mesh renderer**. Backend data remains unchanged.
