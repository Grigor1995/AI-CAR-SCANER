# Cross Platform Compatibility

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

| Target | Scope | Status |
|---|---|---|
| Shared Python backend Linux | Complete common regression + HTTP smoke | See REGRESSION_TEST_REPORT |
| PySide6 Linux offscreen | Five Desktop groups; timing fixture | See evidence |
| Windows EXE/installer | Source APIs unchanged; no Windows runner | NOT VERIFIED |
| Android | No source/dependency/assets changed; consumes same backend contract | PASS: cached Gradle build/test + current lint; device NOT RUN |
| iOS | No source/dependency/assets changed; Xcode unavailable | BLOCKED |
| Native prototype Linux x86_64 | g++20, ASan/UBSan contract executable, ctypes | PASS |
| Native Windows/Android/iOS | Prototype not packaged or integrated | NOT VERIFIED |
| Physical ECU/OBD | No hardware | BLOCKED |

Existing NDK/JNI or Swift wrappers were not invented. No C++ runtime requirement
is added to Desktop installer or mobile build. No unsupported all-vehicle claim.
