# GitHub UI issues #18–#23 — fix audit (2026-10-26)

Review PR: [#28](https://github.com/Grigor1995/AI-CAR-SCANER/pull/28)  
Review branch: `fix/issue-18-23-ui-parity-20261026`

This is a code-level reconciliation of the open product issues, not a claim of completed Windows/Android/iOS native rendering. GitHub Actions CI and Desktop Full QA failed on the PR, but did not supply usable job logs through the available connected tooling. **Do not merge before local reproduction and test sign-off.**

| Issue | Requested outcome | Implemented in review branch | Remaining proof / gap |
|---|---|---|---|
| [#18](https://github.com/Grigor1995/AI-CAR-SCANER/issues/18) | Android 3D UI matches Desktop | Tile/card spacing compacted, existing shared 3D assets retained, icon sizes now respect caller, neon palette aligned | Android emulator screenshots and side-by-side full-screen comparison still needed |
| [#19](https://github.com/Grigor1995/AI-CAR-SCANER/issues/19) | Replace BMW-style vehicle/menu icon with app icon neon blue | Desktop vehicle tile now uses `AI-Car-Scanner-mobile.png`; Android vehicle/menu tiles now use `ic_launcher_foreground`; iOS maps menu/vehicle to shared launcher-car artwork | Verify **visual content** of committed binary icon assets on all platforms, and regenerate any remaining BMW-specific binaries if present. Original PNG/WEBP/ICO launch assets not rewritten by this branch |
| [#20](https://github.com/Grigor1995/AI-CAR-SCANER/issues/20) | Settings via Application → Settings only | Existing Desktop Application menu retained; no Desktop header button; Android/iOS overflow menus labelled as Application menu for accessibility | Real UI check that settings remains reachable on narrow screens and does not appear as extra shortcut |
| [#21](https://github.com/Grigor1995/AI-CAR-SCANER/issues/21) | No sliders | Removed four Desktop Live Data `QSlider` widgets, their styling and state; preserved `QDoubleSpinBox` values and EU/US conversion; fixed contradictory earlier test | Desktop Qt widget test / full regression must run |
| [#22](https://github.com/Grigor1995/AI-CAR-SCANER/issues/22) | Real vehicle images in neon-blue style | Real-backend car photos are now prioritized on Android/iOS and already loaded asynchronously on Desktop; added consistent neon studio frame to all three clients; original photo pixels and credit remain unchanged | Backend may return a generated fallback. Live remote image coverage and each model/chassis still needs audit; this does **not** claim that every catalog image is a licensed real photo |
| [#23](https://github.com/Grigor1995/AI-CAR-SCANER/issues/23) | Visible design in 3D neon blue | Desktop groupboxes/buttons/progress now layered gradient+cyan; Android dark color tokens and tiles; iOS color tokens, vehicle frame | All screens, accessibility contrast, light-theme check, GPU/performance and resizing remain |

## Validation added

- `tests/test_issue_18_23_ui_contracts.py`: dependency-free contracts for routing, no sliders, icon size behavior and photo precedence.
- `apps/desktop/tests/test_ui_widgets.py`: updated existing runtime widget regression to assert **no sliders** while keeping numeric-unit controls.
- `apps/desktop/tests/test_vehicle_artwork.py`: verifies preview is QLabel-compatible, keeps pixmap untouched and paints.

A connector-level source-text check confirmed 11/11 relevant structural conditions, but is **not** a substitute for a native build or screenshot validation.

## Run on Windows

From `finalbuild`:

```bash
git fetch origin
git switch fix/issue-18-23-ui-parity-20261026
python -m pytest -q tests/test_issue_18_23_ui_contracts.py
python -m pytest -q apps/desktop/tests/test_ui_widgets.py apps/desktop/tests/test_vehicle_artwork.py
python -m apps.desktop.main --with-backend
```

For Android Emulator (with the Desktop local backend running), from `finalbuild/apps/mobile-android`:

```bash
./gradlew :app:assembleDebug :app:testDebugUnitTest -PapiBaseUrl=http://10.0.2.2:8001/
./gradlew :app:installDebug -PapiBaseUrl=http://10.0.2.2:8001/
```

Use Xcode + iOS Simulator for actual SwiftUI compilation and UI capture.

## Scope notes

- The issue's phrase "no sliders" is interpreted as **parameter slider widgets**, not content scrolling or wheel navigation needed for accessibility.
- Icons are sourced from existing packaged **app artwork**; this branch does not replace all image assets. A before/after visual review is required to confirm no BMW branding remains.
- "3D" refers to layered neons, gradient and elevation styles; it does **not** claim full three-dimensional vehicle CAD/mesh rendering.
- Preserve real-photo metadata and correct model identity, never imply a generated model illustration is a verified photograph.

Current merge gate: **HOLD** until CI/job failure reasons are known and Desktop, Android and iOS validations pass.
