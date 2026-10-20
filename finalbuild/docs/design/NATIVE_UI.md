# Native automotive dashboard

The supplied 15-screen design guides the navy/cyan panels, vehicle hero,
semantic red/green/violet counters, primary blue controls, top section navigation
and mobile bottom navigation. Existing diagnostics and backend contracts remain
connected; reference-image numbers are never inserted as measured data.

## Screens and behavior

- Home/Summary: model/chassis-matched transparent car portrait, recorded DTC/test/
  hypothesis counts, quick actions and progress derived from actual test results.
- Vehicle selection: catalog selectors, generated model artwork, Desktop search
  and portrait thumbnails. Offline catalog warnings remain visible.
- Device connection: existing BLE/USB/Wi-Fi and simulator controls. A graphic or
  selected vehicle never implies that an adapter is connected.
- Symptoms/DTC: existing editing/analysis actions plus a dedicated DTC overview.
- AI analysis: backend hypotheses and supporting evidence. No illustrative
  confidence percentages or false component confirmations.
- Guided tests: recommended tests, prerequisites/safety notes, notes and explicit
  PASS/FAIL/INCOMPLETE entry. Desktop and iOS offer semantic result cards.
- Live Data: independent traces per actual channel. Desktop handles both `pid`
  and acquisition `channel` fields and allows channel selection/additional widgets.
  Simulator samples are labelled. Android charts use real adapter samples; iOS
  polls the backend acquisition endpoint while its Live Data screen is visible.
- Reports/History: reopen sessions from the backend; Desktop exports native PDF,
  HTML or JSON. Mobile clients share actual session records through native sheets.
- Teach AI: repair notes. Desktop saves drafts and can ingest them as reference
  material; mobile clients save/share drafts on the device. This does not train
  an AI model or imply a completed cloud sync.
- Settings: existing language/theme/backend controls remain native. Dark/light
  appearances and EN/RU/HY choices are retained. New section labels are localized.

The browser/PWA app and its static-only `render.yaml` remain removed. Hosted API
connections remain supported by the native apps.

## Windows cleanup and fonts

The backend worker explicitly uses one Uvicorn worker regardless of inherited
WEB_CONCURRENCY. Desktop shutdown targets only its owned Windows process tree,
waits, and closes the parent log handle in a finally block. The check script
retries transient PermissionError locks for two seconds; a persistent lock keeps
the diagnostic folder and emits a warning without replacing the original test
result. Tests simulate both transient and persistent locks.

Desktop styles use positive point sizes, and QApplication receives an explicit
10-point base font. Windows rendering still needs local visual confirmation.

## Validation

From `finalbuild` with backend/Desktop development requirements installed:

```sh
QT_QPA_PLATFORM=offscreen python -m pytest -q tests apps/desktop/tests --ignore=apps/desktop/tests/test_ui_widgets.py
python scripts/check_local_backend.py
```

Desktop rendering was inspected in dark/light modes using a real backend
session with P0302, actual analysis, recommended tests, and labelled simulator
samples. Tests cover quick navigation, isolated signal channels, report escaping,
native PDF contents, and process/log cleanup. The existing separate Qt widget
suite can intermittently crash during native interpreter teardown.

Android was built with JDK 17 / SDK 36 using:

```sh
cd apps/mobile-android
./gradlew :app:compileDebugKotlin :app:testDebugUnitTest :app:assembleDebug
```

The debug build and 76 unit tests passed. A device/emulator visual review and
instrumentation run have not been performed. In the cloud, SDK/JDK/download and
build caches are outside the repository; no local paths are saved into sources.

Swift source syntax was parsed; native compilation, the new telemetry decoding
test, and iOS simulator rendering require macOS/Xcode and were not run here.
Follow `apps/mobile-ios/README.md` for XcodeGen and xcodebuild commands. This is
not a pixel-perfect acceptance claim for all platforms or a release-signed build.
