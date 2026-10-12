

## Native client icon and parity follow-up — 2026-10-12

- Added an iOS `Assets.xcassets/AppIcon.appiconset` using the existing `finalbuild/assets/ai-car-scanner-icon.png` artwork and configured XcodeGen to compile `AppIcon`.
- Android's current launcher image is byte-identical in Git to `finalbuild/assets/AI-Car-Scanner.webp`; the Desktop PyInstaller specs already package the corresponding ICO artwork.
- Expanded `finalbuild/PLATFORM_FEATURE_PARITY.md` to identify real gaps rather than describe the clients as fully equivalent.
- **Full functional parity is not complete.** Session history/reopen, remote telemetry/simulator UI, adapter lifecycle parity, ECU/CAN network discovery, reports/export, and AI provider/live-data UI still need implementation on mobile. Desktop UI localization is also incomplete.
- **Validation not run for this update:** no iOS/XcodeGen build, Android Gradle build, Desktop test suite, or end-to-end device/backend test was executed. The PNG is configured as a 1024x1024 AppIcon source; the iOS build must confirm the asset catalog accepts it.
