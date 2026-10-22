# AI CAR SCANNER — Cross-platform Neon Automotive UI

> Integration note (2026-10-22): current native clients retain the newer transparent PNG portraits and privacy-aware UI. Desktop may use a matching SVG only when its PNG is absent. The historical SVG/WebView rendering proposal below does not replace the current Android/iOS image renderer. See [branch merge review](../testing/branch-merge-review-2026-10-22.md).

## Visual reference and scope
The design reference supplied by the product owner shows a dark navy automotive
dashboard with electric-blue/cyan navigation and outlines, violet AI indicators,
green PASS states, red FAIL states, amber INCOMPLETE states, rounded panels and
prominent vehicle imagery. It also shows a light option.

This feature branch is a **native UI styling and reusable-panel pass**, not a
promise of pixel-perfect implementation of all fifteen reference screens.
Existing production workflows remain wired to their current APIs/ViewModels.
Displayed measurements, DTCs, confidence scores, estimates and diagnostic
outcomes must always come from actual session data and never from the
illustrative values in the design mockup.

| Feature | Desktop PySide6 | Android Jetpack Compose | iOS SwiftUI |
|---|---|---|---|
| Navy/electric blue dark palette | Qt QSS | Material3 darkColorScheme | AutomotivePalette + gradient |
| Matching light palette | Qt QSS | Material3 lightColorScheme | System light + white cards |
| Branded header | Dashboard with tracked icon | Existing diagnostic header | Navigation header |
| Accent outlines/cards | QGroupBox, tabs, lists | Cards with BorderStroke | AutomotiveCardStyle |
| Navigation | Existing 7-item left rail | Existing session tabs | Scrollable button tabs |
| Vehicle selection | Existing catalog dialog | Existing vehicle form | Existing picker fields |
| DTCs, hypotheses, tests | Existing APIs/pages | Existing ViewModel/tabs | Existing ViewModel/views |
| PASS/FAIL/INCOMPLETE | Existing values | Status-colored selection | Existing TestSheet |
| Settings EN/RU/HY | Existing QSettings | Existing AppSettingsStore | Existing settings binding |
| Reports / Learn-AI extras | Not newly implemented | Not newly implemented | Not newly implemented |

**Existing functionality preserved:** vehicle catalog; W211/LPG diagnostic case;
symptom/DTC collection; analysis; evidence and hypotheses; result recording;
device adapters; telemetry; backend URL configuration and language/theme settings.

## Local validation — do not use CI/CD

### Desktop (Windows Git Bash, Python 3.14 .venv)
From finalbuild after checking out this feature branch:

```bash
bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90
python scripts/real_ui_acceptance.py --mode source --hold-seconds 8
# To check packaging (optional, can take time):
bash scripts/build_desktop_git_bash.sh
python scripts/real_ui_acceptance.py --mode all --exe dist-release/icon-preview/AICarScanner.exe --hold-seconds 8
```

Look for readability and text wrapping at 100%, 125% and 150% scaling,
7 pages, a visually recognizable car icon, taskbar/window icon matching,
EN/RU/HY settings, and dark/light appearance. Check the output of
`desktop-test-reports/real-ui-acceptance/report.html`.

### Android (Windows, Java 17 and configured SDK)
From `finalbuild/apps/mobile-android`:

```bash
./gradlew.bat :app:assembleDebug :app:testDebugUnitTest
./gradlew.bat :app:connectedDebugAndroidTest
```

Use a running Android emulator for connected tests. Check the tab row and
bordered cards at small screen widths, font scaling and when the system is
in light/dark mode. Verify BLE/USB/Wi-Fi controls still work as before.

### iOS (macOS/Xcode or hosted simulator)
From `finalbuild/apps/mobile-ios`:

```bash
xcodegen generate
xcodebuild test -project AICarScanner.xcodeproj -scheme AICarScanner -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' CODE_SIGNING_ALLOWED=NO
```

Confirm SwiftUI compilation, tab selection, keyboard/scroll behavior, sheet
presentation, VoiceOver reading order, dark/light Settings and safe-area layout.

## Release decisions
This branch must not be merged to `main` until:
- Desktop source tests and **visible GUI** acceptance PASS on Windows.
- Android debug build/instrumented checks PASS on an emulator.
- iOS builds and native tests PASS on an iOS simulator.
- Product-owner review confirms the styling and outstanding screens.
- No regressions to locale, API contract or car diagnostic results.

All tests are local. This branch intentionally does not touch
`.github/workflows/` or execute CI/CD.
