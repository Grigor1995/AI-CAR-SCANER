# AI CAR SCANNER — demo and QA presentation

## Desktop and mobile mini demo — 26 October 2026

[Download the 8-page PDF](AI-Car-Scanner-UI-Demo-All-Platforms-2026-10-26.pdf) (3.37 MB).
Includes the five Desktop pages below, Android menu/vehicle source-based
illustrations, archived Android Compose QA captures, and iOS source-based
illustrations. Captions distinguish these: the mobile illustrations are not
emulator/Simulator screenshots, and the Android analysis/tests captures come
from the earlier Robolectric QA run. Fresh full-app mobile runtime captures
remain pending; the cloud emulator did not provide a reliable capture session.
The app launcher now uses the original monochrome D&A TOOL logo on all three
platforms; menu icons and neon vehicle illustrations retain their existing style.

## Current UI mini demo — 26 October 2026

[Download the 5-page PDF](AI-Car-Scanner-UI-Demo-2026-10-26.pdf) (1.53 MB).
Fresh screenshots of the Desktop UI at `4f596b0`: editable main menu, neon vehicle
artwork, analog Live Data, guided tests and recalculated hypothesis scores.
Screens are rendered from the real Qt widgets with seeded demonstration data;
no physical adapter, vehicle or AI-provider connection is claimed.

## Earlier full presentation

Prepared **22 October 2026**, after hiding internal Session IDs from the native
clients and user-facing report exports.

Open [the 22-slide PowerPoint deck](AI-Car-Scanner-Demo-Report-2026-10-22.pptx).
The presentation is in Armenian with English technical terms. It includes the
product walkthrough, architecture, privacy change, native UI captures, actual
source/log evidence, scoped coverage, fixes and remaining validation work.

[Slide overview](slide-overview.png) · [Evidence summary](evidence-summary.json)
· [Slide inventory and speaker notes](slides-manifest.json)

## What changed

- Desktop dashboard/diagnostic/history, Android report/history and iOS
  header/report/history no longer display a complete or truncated Session ID.
- PDF/HTML/JSON and mobile shared report snapshots omit `session_id` fields,
  recursively. The internal model/API/persistence ID stays intact.
- History selection/reopening continues to use the internal ID.
- Regression tests check rendered labels, PDF content, export data preservation
  and unchanged internal objects.

This is presentation/export privacy, not an authentication change. API access
control and physical-device validation remain separate work.

## Latest validation after the privacy change

| Scope | Result |
|---|---|
| Main Python | 541 passed, 1 PostgreSQL/pgvector integration skipped |
| Backend/device/protocol coverage | 97.42% statements; 87.52% branches |
| Desktop | 341 passed; all processes exit successfully |
| Desktop coverage | 90.14% inventory; 91.09% production core |
| Android JVM | 89 passed |
| Supplemental Android native UI | 14 passed; combined run has 103 cases, 0 failures |
| Android coverage | Standard JVM report: 33.83% lines; not full connected UI coverage |
| Android build/lint | Debug APK + androidTest compilation pass; 0 lint errors, 21 warnings |
| iOS | 10 Swift files pass syntax parsing; 29 XCTest cases declared but not run |

The earlier full audit's startup, benchmark and dependency-audit findings are
included with their original scope. The privacy patch does not change those
components; it does not represent a new physical hardware or Xcode test run.
Detailed methodology and remaining gaps:
[full QA audit](../testing/full-qa-audit-2026-10-21.md).

## Screenshot provenance

- `desktop-*.png`: actual PySide6/Qt application output captured offscreen using
  a seeded diagnostic dataset and mocked API/storage boundaries. No live OBD
  hardware or connected production backend is claimed in these images.
- `android-*.png`: actual Compose UI rendering and interaction checks using the
  cloud Robolectric API-35 native-graphics harness and fixture data. These are
  not photographs or emulator/device screenshots. Some slides use clearly
  captioned excerpts of the captures.
- `source-privacy.png`: a native Qt read-only viewer displaying the actual
  `apps/desktop/models.py` export helper; not presented as an IDE capture.
- `test-evidence.png` / `backend-evidence.png`: native Qt viewers displaying
  completed test/startup logs. The source logs are in `evidence/`.
- `cover-car.png`: existing transparent project artwork, not a UI capture.
- **No iOS screenshot was invented:** macOS/Xcode was unavailable.

Internal Session ID values are not shown in the captured UI or the deck. The
engineering slides discuss the `session_id` field name to explain the change.

## Rebuild

Install the optional presentation dependencies:

```bash
python -m pip install -r finalbuild/docs/demo/requirements.txt
python finalbuild/docs/demo/build_demo_report.py
```

The generator uses DejaVu Sans for Armenian/Latin/Cyrillic text. Install that font
if regenerating on a machine that does not have it. Presentation text, cards,
architecture and coverage diagrams remain editable; screenshots are embedded.

The generator reopens the PPTX, checks its slide count and shape bounds, and
creates `previews/` plus the overview image using the same layout definitions.
**Those previews are layout previews, not a native PowerPoint/LibreOffice render.**
The PPTX has not been opened in a native PowerPoint renderer in this cloud.

To recapture the Desktop UI after changing its code (project Qt/dev dependencies
required):

```bash
python finalbuild/docs/demo/capture_desktop_demo.py
python finalbuild/docs/demo/build_demo_report.py
```

Android captures were produced by supplemental cloud tooling. To validate the
committed UI tests on your own emulator/device, run from
`finalbuild/apps/mobile-android`:

```bash
./gradlew :app:connectedDebugAndroidTest
```

Raw logs retain their original run dates. The presentation date is the date of
packaging the deck. Test counts across suites must not be summed as unique cases.
