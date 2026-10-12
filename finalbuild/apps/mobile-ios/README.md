# AI CAR SCANER — Native iOS

Native SwiftUI client for the existing diagnostic platform.

## Current capabilities

- DiagnosticSession-based flow and existing backend API.
- Vehicle catalog and cascading vehicle selection.
- Create and update vehicle.
- Add, edit and delete symptoms.
- Add, edit and delete DTCs.
- Deterministic analysis results: evidence, hypotheses and next diagnostic tests.
- PASS / FAIL / INCOMPLETE test recording.
- Activity and audit log.
- English, Russian and Armenian UI.
- Dark and light theme.
- Backend URL setting.
- Native CoreBluetooth BLE adapter discovery foundation.

See the shared client feature contract in [PLATFORM_FEATURE_PARITY.md](../../PLATFORM_FEATURE_PARITY.md).

## Build

The project is described by project.yml and targets iOS 17+.

Install XcodeGen and generate the Xcode project:

~~~bash
brew install xcodegen
cd finalbuild/apps/mobile-ios
xcodegen generate
open AICarScanner.xcodeproj
~~~

## Backend

Default URL: https://ai-car-scaner.onrender.com

For a physical iPhone, set the backend to a reachable Mac/LAN address from Settings.

## Adapter limitations

Current iOS code supports BLE adapter discovery only; it does not yet connect to the discovered adapter or stream live OBD data. Wi-Fi/TCP OBD connection and ELM327 command flow are not implemented. Generic USB OBD is not implemented; iOS accessory access may require supported external-accessory hardware.

## Test report

The latest validated simulator run is documented in [TEST_REPORT.md](TEST_REPORT.md). The native iOS workflow runs on macOS with XcodeGen + Xcode and executes XCTest on an iOS Simulator. API tests use URLProtocol mocks and do not require a live backend.
