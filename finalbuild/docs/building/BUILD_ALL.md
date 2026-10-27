# Build Desktop, Android and iOS

One repository entrypoint: `build.py` at the **repository root**. It uses local
toolchains and can be invoked by absolute path from any working directory.
CI/CD workflow configuration and the remote `--ci`/`--ref` dispatch options have
been removed. The builder does not submit jobs or publish artifacts remotely.

## Platform requirements

| Target | Local host/toolchain | Output |
|---|---|---|
| Desktop | Windows, Python 3.12+ | ZIP with `AICarScanner.exe` and `backend_service.exe` |
| Android | Windows/Linux/macOS, JDK 17, Android SDK 36 | Debug APK |
| iOS | macOS, Xcode and XcodeGen | Unsigned Simulator `.app` ZIP |

A single Windows machine cannot compile iOS. Run the same entrypoint on Windows
for Desktop + Android and on macOS for iOS. Outputs remain in local `artifacts/`.

## Local build

First install the native toolchains, then check them without installing or
building anything:

```bash
python build.py --check
```

The preflight explains unavailable platforms and missing SDKs. On Windows with
Android Studio/JDK configured:

```bash
python build.py --targets desktop android --with-tests
```

On macOS with Android SDK/JDK and Xcode/XcodeGen:

```bash
python build.py --targets android ios --with-tests
```

To build whatever is available on the current machine:

```bash
python build.py --skip-unavailable --with-tests
```

Unavailable targets remain explicitly `UNAVAILABLE`; the overall result is
`PARTIAL`, never a misleading full PASS. Without `--skip-unavailable`, missing
requested targets produce a nonzero exit code even when the available targets
build successfully. If no target can build, the command fails regardless.

Running `python build.py` without options requests all three targets. Missing
native toolchains are not silently downloaded or marked successful. Windows
Desktop + Android can be built in one Windows run; iOS needs a separate macOS run.

### Already inside finalbuild/apps/mobile-android?

Git Bash, from any repository subfolder:

```bash
cd "$(git rev-parse --show-toplevel)"
python build.py --targets desktop android --with-tests
```

Or invoke the root entrypoint directly from that Android directory:

```bash
python ../../../build.py --targets android
```

This avoids requirements-file and working-directory problems.

## Toolchains and dependency setup

### Desktop

- Windows x64 and Python 3.12+; Python 3.14 x64 is supported.
- The builder creates/reuses `.build-tools/desktop-venv/` and installs runtime
  dependencies there. With `--with-tests`, backend/Desktop dev dependencies are
  also installed. It does not alter the user's activated environment.
- Both canonical PyInstaller specs are built. Icon formats are staged outside
  source; tracked artwork is not overwritten. A locally edited Desktop PNG is
  honored as in the existing Windows builder.
- To deliberately use dependencies already installed in your current Python,
  add `--no-install`.
- The Desktop ZIP contains both executables; extract them together and run
  `AICarScanner.exe --with-backend`. Local AI model/server binaries remain a
  separate runtime configuration; no multi-gigabyte model is downloaded.

### Android

- JDK 17 or 21 recommended (this Gradle version supports JDK 17–23).
- Install SDK platform **android-36**, build-tools **35.0.0** and platform-tools
  in Android Studio's SDK Manager; accept their SDK licenses.
- Set `ANDROID_HOME` / `ANDROID_SDK_ROOT`, or use the project's `sdk.dir` in
  `local.properties`. Standard Android Studio SDK locations are also detected.
- Set `JAVA_HOME` to the JDK when `java` on PATH points elsewhere.
- The bundled Gradle wrapper downloads its own Gradle/dependencies. Android
  Studio does not have to be open. No Python runtime/dev dependencies are needed
  just to build Android.
- Output is a debug-signed APK suitable for local testing. This does not create
  a Play Store release or configure a private release signing key.

### iOS

- macOS, full Xcode selected via `xcode-select`, an accepted Xcode license and
  an installed iOS Simulator SDK.
- Install XcodeGen with `brew install xcodegen`.
- With `--with-tests`, install an available iPhone simulator runtime. The runner
  discovers an available iPhone destination instead of hard-coding its model.
- Project generation uses the canonical `project.yml`; generated Xcode project
  files are ignored by Git.
- Output is an **unsigned simulator app**, not an installable iPhone IPA or
  App Store upload. Device/Store distribution needs your Apple team, profiles
  and signing/export configuration; those credentials are not bundled here.

## Logs, artifacts and result codes

Each run has its own directory; previous artifacts are not deleted:

```text
artifacts/<UTC-run-id>/
  build-summary.json
  desktop/
    build.log
    AI-Car-Scanner-Windows.zip
  android/
    build.log
    AI-Car-Scanner-Android-debug.apk
  ios/
    build.log
    AI-Car-Scanner-iOS-Simulator.zip
    TestResults.xcresult/          # when iOS tests run
```

The JSON records requested targets, host, test mode, individual outcomes, output
sizes and SHA-256 hashes. Compiler/install/test errors produce a `FAIL` entry and
nonzero exit code. Other independent requested targets still run. Required
artifacts are checked after command completion; an empty/missing artifact is a
failure. Unique run/work directories prevent stale outputs from being mistaken
for a new package.

- `0`: all selected targets passed, or an explicitly allowed partial run has at
  least one successful target; inspect the summary for `PARTIAL`.
- `1`: build/setup failure, or no target was buildable.
- `2`: missing required target/toolchain, or invalid CLI usage.
- `--check`: returns `0` only when every selected toolchain is ready, otherwise `2`.

The `.build-tools/` directory holds disposable build caches/work/isolated Python;
`artifacts/` holds the output. Both are ignored by Git. You may remove those
**generated** directories manually to reclaim disk space when no build is active.

## Tests and validation scope

`--with-tests` enables the existing isolated Desktop regression suite with the
90% production-core gate, Android JVM tests + lint, and iOS XCTest with coverage.
It does not attach OBD hardware or turn simulator builds into device validation.
The runner's own tests cover independent failure propagation, missing platforms,
strict vs partial status, output hashes, no-side-effect preflight, missing
artifacts, SDK paths, supported Java, simulator selection, package contents and
rejection of removed remote-dispatch options.

Development validation for this change includes an actual Android APK build
through the new root command with JVM tests/lint. Windows EXE packaging and iOS
Xcode execution require their native runners; this Linux development environment
cannot certify Windows packaging or iOS execution.

### Recorded validation for this implementation

- Build-runner contract tests: **15 passed**.
- Full main Python regression suite: **589 passed, 2 skipped**.
- Actual root-command execution: `python build.py --targets android --with-tests`
  completed successfully and produced a **53,453,588-byte debug APK**. Its
  SHA-256 was recomputed and matched `build-summary.json`.
- Android JVM tests: **89 passed**; `lintDebug` passed.
- These recorded counts describe the original builder implementation, not the
  current application. Windows packaging and iOS execution require local
  validation on their respective operating systems.

### Build progress and interruption

Commands stream their output to the terminal and retain the complete UTF-8
`<run>/<target>/build.log`. Desktop test logs, JUnit and coverage reports are
kept in `<run>/desktop/test-reports/`, including failed tests.

Ctrl+C stops the builder-owned command tree, writes `CANCELLED` to
`build-summary.json`, marks remaining targets `NOT_RUN`, and exits with code
130. Previously completed artifacts remain available. An interrupted Android
build is not evidence of a compilation failure.

### Android backend URL

For a local backend reached from an emulator:

```bash
python build.py --targets android --with-tests --android-api-url http://10.0.2.2:8001/
```

The URL is embedded into the Android build. Physical phones need the backend's
reachable LAN/HTTPS address. See [OBD setup](../obd/SETUP_AND_API.md).
