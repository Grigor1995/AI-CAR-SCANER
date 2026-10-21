# Native iOS Test Report

## Cloud audit — 2026-10-21

The current source declares **28 XCTest cases**. All 10 Swift files pass a
Tree-sitter Swift syntax check in the Linux cloud environment. XCTest, Swift
compilation/type checking, simulator behavior and numeric iOS coverage were
**not executed or measured** in this audit because Xcode/macOS is unavailable.
Do not treat the historical CI baseline below as validation of the current UI.

The audit fixes result entry so failed requests keep the sheet/notes available
for retry, duplicate submissions are disabled while loading, and successful
submissions return to the updated analysis. Selected-language result-label
assertions have also been added; these require the next Xcode test run.

## Current status

The native iOS CI suite has a previously verified baseline of **2 tests passed, 0 failures** (run #14). This branch expands the suite with URLProtocol-backed API contract tests; its final status must be taken from the GitHub Actions run triggered by this commit.

## Test environment

- Workflow: Native iOS Tests
- Runner: `macos-15`
- Xcode: latest installed on the runner (baseline: 16.4)
- Simulator: iPhone 16, latest available iOS runtime
- Deployment target: iOS 17+
- Language mode: Swift 5
- Code coverage collection: enabled
- Result bundle: `TestResults.xcresult`, uploaded as `ios-xctest-results`

## Test matrix

| Test | Scope | Expected result |
|---|---|---|
| `testVehicleRoundTrip` | Vehicle Codable serialization | Fields survive encode/decode |
| `testLanguages` | EN/RU/ARM labels | Labels match app contract |
| `testVehicleCatalogRequestAndDecode` | API GET path and empty catalog response | Correct path; decodes empty list |
| `testCreateSessionSendsVehiclePayload` | Session POST method/path/body and response decoding | Vehicle fields are sent and session is decoded |
| `testGoldenCaseAnalysisUsesSelectedLanguageAndPreservesUncertainty` | P0302 LPG-misfire analysis request/response contract | Russian language is sent; hypotheses remain possible rather than confirmed |
| `testHTTPErrorIsSurfaced` | Non-2xx backend response | HTTP status and body are surfaced |
| `testInvalidBaseURLThrows` | URL validation | Invalid URL is rejected |

API tests use a custom `URLProtocol` with an ephemeral `URLSession`. They do not call a live backend or depend on network availability.

## Diagnostic golden-case contract

The mocked golden case represents a 2006 Mercedes-Benz W211 E350, M272 3.5, petrol + LPG, DTC P0302, smooth on petrol and misfire under low-RPM load on LPG. It checks that the client decodes the evidence/hypothesis contract without converting possible causes into confirmed component failures. This is a **client contract test**, not proof of backend diagnostic accuracy; backend golden-case regression tests remain the authoritative reasoning tests.

## CI procedure

1. Checkout source.
2. Install XcodeGen and generate `AICarScanner.xcodeproj`.
3. Print Xcode/XcodeGen versions.
4. Run XCTest on an iOS Simulator with code coverage enabled.
5. Upload the `.xcresult` bundle even if tests fail.

Workflow: `.github/workflows/ios.yml`.

## Coverage policy

Coverage is collected and the result bundle is retained, but a numeric iOS coverage gate is not yet enforced. The suite is still being expanded; a percentage threshold should be introduced after API, ViewModel, golden-case, OBD transport and UI tests cover meaningful behavior. Do not infer a coverage percentage from the test count.

## Issues found and fixes in expanded API tests

- The first expanded run exposed that invalid URL bases were not rejected early enough. URL validation now requires an explicit `http` or `https` scheme and a host before building the endpoint.
- The URLProtocol POST test now reads request payloads from either `httpBody` or `httpBodyStream`, because URLSession may surface streamed request bodies in the protocol layer.
- The latest CI result is the source of truth for whether these fixes pass; do not mark this branch green until the workflow completes successfully.

## Remaining phases

- ViewModel lifecycle tests using injectable API dependencies.
- PASS / FAIL / INCOMPLETE result recording tests.
- OBD adapter abstraction and deterministic BLE/Wi-Fi transport tests.
- SwiftUI UI tests for vehicle selection, symptom/DTC entry and analysis.
- Physical-device smoke test.
- Inspect the `.xcresult` coverage report and establish a measured gate.
