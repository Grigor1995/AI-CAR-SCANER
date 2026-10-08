# Native iOS Test Report

## Status

**PASS**

Final successful GitHub Actions run:

- Workflow: Native iOS Tests
- Run: #14
- Commit: `6c81ba64f916987036d018dcdc9b7fa7b28e0733`
- Runner: `macos-15`
- Xcode: `16.4`
- iOS Simulator SDK: `iPhoneSimulator18.5`
- Test destination: iPhone 16 / latest simulator image
- Build configuration: Debug
- Swift language mode: Swift 5
- Code coverage: enabled
- Result bundle: `TestResults.xcresult`

## XCTest result

| Suite | Tests | Failures | Result |
|---|---:|---:|---|
| AICarScannerTests | 2 | 0 | PASS |
| AICarScannerTests.xctest | 2 | 0 | PASS |
| All tests | 2 | 0 | PASS |

Measured XCTest execution time: **0.004–0.005 s**.

Final xcodebuild result:

`** TEST SUCCEEDED **`

## Tests

### testVehicleRoundTrip
Validates JSON Codable round-trip for the canonical Mercedes W211 diagnostic vehicle:

- Mercedes-Benz
- E-Class
- W211
- 2006
- M272 E35 3.5
- petrol + LPG
- ME9.7

### testLanguages
Validates the three UI language identifiers/labels:

- EN
- RU
- ARM

## Build validation

The workflow also validates the native project before XCTest:

1. Checkout source.
2. Install XcodeGen.
3. Generate `AICarScanner.xcodeproj`.
4. Print Xcode/XcodeGen toolchain versions.
5. Build the application and test target.
6. Run XCTest on the iOS simulator.
7. Collect code coverage.
8. Upload the `xcresult` bundle.

All workflow steps passed in the final run.

## Problems found and fixed during test execution

The first CI execution exposed real Swift issues rather than being treated as a false PASS.

### 1. Swift declaration errors

The generated source initially contained malformed declaration separators/newline escapes in Swift files.

Fixed in:
- `DiagnosticViewModel.swift`
- `DiagnosticAPI.swift`

### 2. SwiftUI @State declarations

Several variables were declared on the same line under property wrappers. Swift rejected this with:

`property wrapper can only apply to a single variable`

Fixed by declaring every `@State` property separately.

### 3. Language property collision

The translation struct contained both the stored `language` value and a computed property named `language`.

Fixed by renaming the UI label property to `languageLabel`.

### 4. Symptom edit contract

The UI attempted to assign a complete `Symptom` object to the editable text field.

Fixed to use `symptom.raw_text` and connected the edit operation to the backend PUT endpoint.

### 5. Missing API method

The iOS API layer was missing the native symptom update method.

Added:

`PUT /api/v1/sessions/{session_id}/symptoms/{symptom_id}`

### 6. Missing state-localization helper

The iOS client referenced a helper that only existed in another client.

The native screen now renders the backend session state directly.

### 7. CoreBluetooth Swift 6 isolation warnings

The initial `@MainActor` CoreBluetooth delegate implementation conflicted with nonisolated delegate requirements.

The OBD discovery service was changed to use the CoreBluetooth delegate without incorrectly isolating delegate callbacks to the main actor.

### 8. Simulator application installation

The simulator reported:

`MissingBundleExecutable`

The custom iOS Info.plist did not explicitly declare `CFBundleExecutable`.

Added:

`CFBundleExecutable = AICarScanner`

After this fix, the app installed and XCTest executed successfully.

## Coverage

The workflow invokes XCTest with:

`-enableCodeCoverage YES`

The generated `TestResults.xcresult` is uploaded as the `ios-xctest-results` GitHub Actions artifact.

A numeric coverage gate is **not** enforced yet because the current native iOS suite contains only two contract/model tests. The next iOS test phase should add API, ViewModel, diagnostic-flow, and OBD adapter tests before introducing a percentage threshold.

## Known test scope

Current tests validate the foundation only. They do **not** yet prove:

- real backend HTTP integration
- vehicle catalog loading against a live backend
- diagnostic analysis against real sessions
- BLE adapter communication
- Wi-Fi OBD protocol communication
- physical iPhone behavior
- camera/permissions/accessory behavior
- UI screenshot/pixel parity with Android

These are intentionally separate from the first native build gate.

## Recommended next test phase

1. API request/response tests with URLProtocol mocks.
2. ViewModel session lifecycle tests.
3. Diagnostic golden-case test using `LPG_MISFIRE_001`.
4. PASS/FAIL/INCOMPLETE test-result flow.
5. BLE discovery tests with a fake adapter layer.
6. Wi-Fi OBD transport simulator tests.
7. SwiftUI UI tests for the main diagnostic flow.
8. Physical-device smoke test on a real iPhone.
9. Only then introduce an iOS coverage threshold.

## CI

Workflow file:

`.github/workflows/ios.yml`

The workflow is triggered when the native iOS app changes and on pull requests touching the iOS client.
