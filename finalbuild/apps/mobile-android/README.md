# AI CAR SCANER — Native Android

Native Kotlin + Jetpack Compose client.

Use the shared cross-platform feature contract in [PLATFORM_FEATURE_PARITY.md](../../PLATFORM_FEATURE_PARITY.md) as the canonical feature list and parity tracker.

## Build

Open this directory in Android Studio, sync Gradle, then run the app configuration on an emulator or device.

## Backend

The default API is `https://ai-car-scaner.onrender.com`. It is configured in `app/src/main/java/com/aicarscaner/mobile/data/api/ApiClient.kt`.

For local emulator development only, use `http://10.0.2.2:8001/` when the FastAPI backend is running on the development host.

## Diagnostic result contract

Test results sent to the API must be exactly `PASS`, `FAIL`, or `INCOMPLETE`. Legacy `UNKNOWN` is accepted by the backend only for compatibility and normalized to `INCOMPLETE`.

## Reference dashboard

The native dashboard uses the supplied blue automotive design: transparent model
portraits, status cards, two-column quick actions and five bottom destinations.
**More** opens vehicle selection, symptoms, DTC details, AI analysis, guided tests,
testing progress, custom telemetry widgets, history, repair notes and settings.
Language and theme changes update the current screen immediately. Chart samples,
hypothesis scores and test progress come from the current session and adapter.
Repair notes are saved on the device and can be shared.

Run `./gradlew :app:testDebugUnitTest :app:assembleDebug` to validate and build.
The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.
