# Native automotive UI

Desktop (PySide6), Android (Compose), and iOS (SwiftUI) use the navy, electric-blue,
cyan and violet reference documented on the repository's
`feature/neon-ui-desktop-android-ios` branch at
`4de32cd23a5e314405e800eedf014f44c2fd03c4`. This change reuses its native styling
and vehicle panels; it does not import that branch's backend recovery changes.
The original visual demo screenshots are not included on main; matching to that
original demo still needs visual review.

The browser/PWA app and its static-only `render.yaml` have been removed.
Hosted backend URL settings remain available to the native clients.

## Vehicle portraits

Generated transparent PNG portraits cover the 22 distinct make/model/chassis
combinations in `shared/vehicle_catalog.json`. The canonical copies live under
`assets/vehicle_models`. Names normalize each component to lowercase ASCII
letters/digits and hyphens, joined with underscores. Android bundles copies in
`app/src/main/assets/vehicle_models`; iOS bundles the `VehicleModels` resource
folder. Desktop packaging includes the canonical folder. Run
`python scripts/sync_vehicle_portraits.py` after changing canonical artwork.

All portraits were generated as isolated silver production vehicles in a front
three-quarter view, with model/chassis-specific body proportions and a transparent
background. These are illustrations, not photographs of a user's car or proof of
VIN-level fitment. Unknown models fall back to a generic car/app symbol. Native
image controls preserve aspect ratio and transparency; no web views or network
image services are used.

## Validation

From `finalbuild`, with Desktop and backend development requirements installed:

```sh
QT_QPA_PLATFORM=offscreen python -m pytest -q apps/desktop/tests/test_vehicle_artwork.py
QT_QPA_PLATFORM=offscreen python -m pytest -q apps/desktop/tests --ignore=apps/desktop/tests/test_ui_widgets.py
python -m pytest -q
```

The image tests check catalog coverage, alpha channels, native bundle copies,
unknown-model resolution and actual Qt rendering. Review Desktop at normal and
increased text scaling in both themes. The existing Qt widget test group has a
documented native teardown crash in CI and must be reported separately.

Android needs SDK 36; run `./gradlew testDebugUnitTest assembleDebug` from
`apps/mobile-android`, then review on a device/emulator. iOS needs macOS, Xcode
and XcodeGen; follow `apps/mobile-ios/README.md`. Linux source changes do not
establish that either mobile build or device rendering passed.
