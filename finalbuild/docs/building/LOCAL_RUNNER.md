# Clone-to-run setup runner

Run the root **`runner.py`** from a new terminal. No venv activation, manual pip
commands, administrator privileges or CI/CD dispatch are needed. Git and 64-bit
Python 3.12+ must already be installed (Windows Python 3.14 recommended).

## One-command Windows setup

```bash
git clone --branch main https://github.com/Grigor1995/AI-CAR-SCANER.git
cd AI-CAR-SCANER
python runner.py setup --accept-android-licenses --run
```

`--accept-android-licenses` explicitly accepts Google's SDK licenses without an
interactive prompt. Omit it to review/respond to the licenses in the terminal.
The default setup:

1. Creates/reuses repository-root `.venv`, installs `finalbuild/requirements.txt`,
   runs `pip check` and verifies native Desktop/backend imports.
2. Reuses an existing llama-server/model or downloads the official Windows CPU
   x64 llama.cpp release and the default `Qwen3-8B-Q4_K_M.gguf`. The complete runtime
   directory, including its DLLs, is installed. GPU runtimes can be supplied instead.
3. Finds a working JDK 17–23, including Android Studio's JBR when suitable, or
   downloads an Adoptium JDK 17 into local `.build-tools/setup/jdk` on Windows x64.
4. Reuses an existing Android SDK or installs one under `.build-tools/setup/`.
   Required packages: SDK platform 36, build-tools 35.0.0 and platform-tools/ADB.
   The Java-based command-line tools 19.0 are selected for JDK 17 compatibility.
5. Builds the debug APK with the bundled Gradle wrapper via direct Java invocation.
6. Writes machine-specific `.runner-state.json` only after all requested steps
   succeed. With `--run`, opens Desktop + Backend + local AI afterward.

**First-run downloads can total several GB**, especially GGUF weights and the
Android SDK. Partial downloads are kept as `.part` files and can resume on rerun.
Checksum/revision validation protects newly downloaded model files; Android/JDK
archives use their official manifest checksums, and llama.cpp uses the release
asset digest when provided. ZIP traversal/symlink entries are rejected.
Existing user-supplied files are reused rather than overwritten. A GGUF header
check is not proof of successful inference; use the service check after launching.

Network access to PyPI, Google Android repositories, Adoptium, GitHub,
Hugging Face and Gradle/Maven repositories is required when components are missing.
The model metadata must identify the exact single-file GGUF and its SHA-256;
if that upstream layout changes, setup stops with instructions to use `--model`.

## Reuse saved AI files / choose tool locations

After backing up AI assets outside an old checkout:

```bash
python runner.py setup --model "C:/AI/models/Qwen3-8B-Q4_K_M.gguf" --llama-dir "C:/AI/llama.cpp" --accept-android-licenses
```

External model/runtime directories are referenced directly; copying a 5 GB model
into each clone is unnecessary. Keep the runtime's companion DLLs together.
`--java-home "C:/Tools/jdk-17"` and `--android-sdk "C:/Users/NAME/AppData/Local/Android/Sdk"`
select existing toolchains. Native Windows paths are stored by Python, avoiding
Git Bash environment-path conversion problems.

For a smaller first setup:

```bash
python runner.py setup --skip-android --skip-ai
python runner.py desktop --no-ai
```

`--skip-android-build` prepares the SDK without compiling an APK.
`--with-tests` installs/runs Python and Desktop regressions; when Android is
built, its JVM tests/lint are included. No background build/test job is submitted.
The root `build.py` can also discover runner-managed SDK/JDK locations.

## Daily launch

First terminal:

```bash
python runner.py desktop
```

This uses `.venv` automatically, starts Backend on port 8001 and local AI on 8000,
and opens Desktop. The API binds to `127.0.0.1` by default. Emulator host routing remains available.
Physical LAN phones require an explicit `AI_CAR_BACKEND_HOST=0.0.0.0` override
on a trusted development network; the legacy API is not a public authenticated service. Keep
Desktop/the terminal open while Android uses its backend. Set `--port` during
setup to choose another backend port; the default Android URL follows that port.
`--ai-port` changes the AI port; Backend and AI ports must differ.

Second terminal, after starting an emulator in Android Studio Device Manager:

```bash
python runner.py android
```

The Android command checks backend health **before** building/installing. It
requires one online ADB device, or an explicit `--serial emulator-5554`. It builds,
installs the debug APK, stops the old app process, writes only its backend-URL
preference using debug `run-as`, and launches it. Drafts and other app preferences
are retained; no `pm clear`, uninstall or factory reset is performed.

The default emulator API URL is `http://10.0.2.2:8001/`. Alternatives:

```bash
python runner.py android --reverse
python runner.py android --api-url http://192.168.1.20:8001/
python runner.py android --build-only
```

`--reverse` uses ADB port forwarding and configures Android localhost instead of
emulator routing. A physical phone over Wi-Fi needs the computer's LAN address.
`--build-only` does not need a backend or connected device and does not install.

The runner prepares Android build tools; it does not install Android Studio,
create a device emulator, grant a phone's USB-debug authorization or provision
Windows hypervisor drivers. Use an existing emulator/phone; these OS/device
steps remain explicit. iOS builds still require macOS/Xcode and the local
[build guide](BUILD_ALL.md). Automatic JDK/llama downloads target Windows x64;
other hosts can supply existing tools with the path options above.

## Check and recovery

```bash
python runner.py check
python runner.py check --services
```

The first is read-only and performs no downloads. The second also requires
healthy running backend/AI services. Setup-ready and running-services are
separate states; a stopped backend is never reported as healthy.

Install/build logs are under `.build-tools/setup/logs/`. The state file and
managed tool directories are ignored by Git. They contain local paths, not
project defaults. No user/global PATH, JAVA_HOME, SDK settings or database are
rewritten; environment overrides apply to runner children only. Explicit setup
path flags select alternatives to inherited environment configuration.

An unfinished install returns a nonzero exit code and does not save a new READY
state. Rerun to reuse completed components. A setup lock prevents concurrent
installers; after an abnormal OS/process kill, remove only
`.build-tools/setup/setup.lock` once no setup process is running. Normal Ctrl+C
releases the lock and preserves download parts/logs. Existing Desktop data under
`%APPDATA%/AI-Car-Scanner/` remains separate from clone/venv setup.

## Validation boundary

Contract tests cover resumable/checksummed downloads, archive paths, SDK license
handling, failed-install state, locking, backend checks, direct Gradle invocation
and Android preference preservation. Network restrictions in the Linux cloud
prevented a real GitHub/Hugging Face/Adoptium cold download; Windows-native fresh
installation and emulator acceptance still require a local run. No successful
full Windows setup or model inference is claimed from mocked installer tests.


### Checks performed for this implementation

- Full Python regression: **928 passed, 2 skipped**; focused runner/builder
  contracts after the final launch-lock correction: **56 passed**. Scopes overlap.
- Actual `.venv` creation and its isolated pip were exercised in a temporary
  checkout using a Python installation with bundled ensurepip.
- The runner's direct-Java Gradle path produced a real **168,169,910-byte debug APK**.
- The official Google tools 19.0 ZIP was downloaded, its manifest SHA-1 verified,
  safely extracted, and its SDK Manager CLI successfully executed with JDK 17.
- Static Python checks and documentation links pass. Windows-native installation,
  ADB preference writing on a device, and the blocked model/runtime/JDK cold
  downloads retain the validation limits described above.
