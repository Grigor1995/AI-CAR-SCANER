# AI CAR SCANER — Native iOS

Native SwiftUI client for the existing diagnostic platform. No Flutter is used.

## Current parity

- DiagnosticSession-based flow and existing backend API.
- Vehicle catalog and cascading vehicle selection.
- Create and update vehicle.
- Add, edit and delete symptoms.
- Add and delete DTCs.
- Deterministic analysis results: evidence, hypotheses and next diagnostic tests.
- PASS / FAIL / INCOMPLETE test recording.
- Activity and audit log.
- English, Russian and Armenian UI.
- Dark and light theme.
- Backend URL setting.
- Native CoreBluetooth BLE adapter discovery foundation.

## Build

The project is described by project.yml and targets iOS 17+.

Install XcodeGen and generate the Xcode project:

    brew install xcodegen
    cd finalbuild/apps/mobile-ios
    xcodegen generate
    open AICarScanner.xcodeproj

## Backend

Default URL: http://127.0.0.1:8001

For a physical iPhone, set the backend to the Mac LAN address from Settings.

## Adapter note

Wi-Fi/TCP OBD is the preferred generic iOS transport path. BLE discovery is implemented through CoreBluetooth. Generic USB access is handled separately because iOS accessory support differs from Android.


## Test report

The latest validated simulator run is documented in [TEST_REPORT.md](TEST_REPORT.md).

The native iOS CI workflow runs on macOS with XcodeGen + Xcode and executes XCTest on an iOS Simulator. The test result bundle is uploaded as a GitHub Actions artifact.
