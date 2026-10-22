# Vehicle model artwork and FastAPI auto-recovery (feature branch)

> Integration note (2026-10-22): current native clients retain the newer transparent PNG portraits and privacy-aware UI. Desktop may use a matching SVG only when its PNG is absent. The historical SVG/WebView rendering proposal below does not replace the current Android/iOS image renderer. See [branch merge review](../testing/branch-merge-review-2026-10-22.md).

## Vehicle images
- The curated offline catalog contains **369 rows and 22 distinct make/model/chassis combinations**.
- The feature branch bundles the same 22 SVG artworks independently for:
  - Desktop: `assets/vehicle_models/*.svg` — QtSvg renders local files with a branded fallback.
  - Android: `apps/mobile-android/app/src/main/assets/vehicle_models/*.svg` — embedded WebView opens **only** local SVG assets, JavaScript disabled.
  - iOS: `apps/mobile-ios/AICarScanner/VehicleModels/*.svg` — bundled local WebKit resource, JavaScript disabled.
- A stable lowercase slug of `make_model_chassis.svg` selects the artwork.
- Changing make/model/chassis updates the visual; unknown models use branded/generic fallback.
- **These are stylized model-labelled SVG illustrations, NOT OEM photographs or VIN-verified vehicle likenesses.** For photorealistic model-matched images, add separately cleared/licensed PNG/WebP assets and a metadata/license manifest.
- No vehicle images require external network requests.

## FastAPI recovery
- **Only a Desktop-owned local FastAPI child** (`AI_CAR_BACKEND_URL` local loopback) is eligible for restart after unexpectedly exiting.
- `apps/desktop/backend_recovery.py` supervises in a background thread, with at most 3 attempts per 120 seconds, exponential retry delay, and log entries for attempts/errors.
- `apps/desktop/main.py` registers the supervisor after initial startup, and stops it **before** stopping the backend on normal shutdown.
- `AI_CAR_BACKEND_AUTO_RECOVER=0` disables local process recovery.
- A separate Desktop UI health timer rechecks every 12 seconds, shows `Backend offline` on connection failures and `Backend recovered` when service connectivity returns. Health failures don't spawn endless modal dialogs.
- The app never attempts to spawn or kill a third-party backend, and **cannot restart Render/cloud FastAPI on the server**. Cloud restarts must be handled by hosting infrastructure. Android/iOS still require network to access the actual API.
- The monitor is for crash/exited-process recovery; a live but permanently hung FastAPI process is not killed automatically (avoids disrupting in-flight work without independent hang diagnostics).
- Diagnostic sessions are persisted by the backend's existing state layer; process restart does **not** guarantee restoration of unsaved in-flight transactions. Re-read session state after reconnection.

## Tests (local only, no CI/CD)
```bash
# From finalbuild on Windows with the user's Python 3.14 .venv:
git fetch origin
git switch --track origin/feature/neon-ui-desktop-android-ios

python -m pytest -q tests/desktop/test_backend_recovery.py apps/desktop/tests/test_vehicle_artwork.py
python -m pytest -q apps/desktop/tests/test_ui_pom.py -k 'backend_health_autoreconnect'
bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90

# Visible screenshot acceptance:
python scripts/real_ui_acceptance.py --mode source --hold-seconds 8

# Packaged EXE (after tests pass):
bash scripts/build_desktop_git_bash.sh
python scripts/real_ui_acceptance.py --mode all --exe dist-release/icon-preview/AICarScanner.exe
```
Android:
```bash
cd apps/mobile-android
./gradlew.bat :app:assembleDebug :app:testDebugUnitTest
# emulator must be online
./gradlew.bat :app:connectedDebugAndroidTest
```
iOS requires macOS + Xcode/XcodeGen and a simulator:
```bash
cd apps/mobile-ios
xcodegen generate
xcodebuild test -project AICarScanner.xcodeproj -scheme AICarScanner -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' CODE_SIGNING_ALLOWED=NO
```
Recheck artwork for all catalog variations, 100/125/150% Windows display
scaling, iOS/Android small screens, light/dark mode, and EN/RU/HY settings.

## Recovery manual test
1. Use a **test** instance of the Desktop-owned local backend, not Render.
2. Start Desktop and wait until Backend online; create a disposable test session.
3. Terminate only its child `uvicorn` / `backend_service.exe` process (not the Desktop app and not unrelated services).
4. Expect logged restart attempt, API health to return, and UI to show Backend recovered.
5. Simulate repeated crashes; verify the restart budget prevents an endless process loop.
6. Close Desktop; confirm it does not launch another backend after shutdown.

**Do not merge to main or publish v1.0 release solely on static checks.**
Validate Windows Desktop/Android/iOS runtimes first. No GitHub Actions were run.
