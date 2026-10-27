# Clean Windows setup — Desktop, Backend and Android

Use a **new Git Bash terminal** after closing old Desktop/backend processes and
terminals that reference the deleted virtual environment. Commands below assume
Python 3.14, Git, Android Studio, Android SDK 36 and JDK 17 are installed.
Python dependencies and Gradle dependencies are installed locally; no CI/CD is used.

## Before deleting the old checkout

Copy these to a location **outside** the checkout first:

- `finalbuild/models/*.gguf`: model weights are ignored by Git and are not restored
  by cloning. The default model is `Qwen3-8B-Q4_K_M.gguf`.
- The entire llama.cpp runtime directory (for example
  `finalbuild/tools/llama.cpp/`), including `llama-server.exe` and companion DLLs.
  Copying just the EXE can leave the runtime unusable.
- Any uncommitted changes, personal files or reports you want to retain.

Diagnostic sessions/local profiles are stored separately under
`%APPDATA%/AI-Car-Scanner/`; Desktop preferences are also outside the checkout.
Deleting the checkout and venv does not reset them. Keep a backup of that folder
if its data matters; these setup commands do not delete application data or clear
Android's saved drafts/preferences.

## 1. Fresh clone and virtual environment

After moving aside/deleting the old `git` checkout, in a new Git Bash terminal:

```bash
mkdir -p ~/Desktop/AI-CAR-SCANER
cd ~/Desktop/AI-CAR-SCANER

git clone --branch main https://github.com/Grigor1995/AI-CAR-SCANER.git git
cd git

py -3.14 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip

cd finalbuild
python -m pip install -r requirements.txt
```

If the Windows `py` launcher is not installed, verify `python --version` in the
new terminal and use `python -m venv .venv` instead of the `py` command.
Do not run creation from an old, deleted venv.

`requirements.txt` installs backend and native Desktop runtime requirements,
including PySide6, Pillow and the common PDF-report dependencies. Gradle does
not use this Python virtual environment.

## 2. Restore the offline AI runtime

Put the saved files back here:

```text
finalbuild/
  models/
    Qwen3-8B-Q4_K_M.gguf
  tools/
    llama.cpp/
      llama-server.exe
      ...companion DLLs from the same release...
```

If needed, obtain the appropriate Windows x64 runtime from the
[official llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases/latest).
Use a compatible CPU runtime first, or the GPU package matching your hardware.
The runtime and GGUF weights are not Python packages and are not installed by pip.
The launcher finds the directory shown above automatically.

From `finalbuild`, verify the executable itself can load before launching:

```bash
./tools/llama.cpp/llama-server.exe --version
```

For an external runtime/model location, the launcher also supports
`LOCAL_LLM_SERVER_PATH` and `LOCAL_LLM_MODEL_PATH`. In Git Bash, use a native
Windows path such as `C:/AI/llama.cpp/llama-server.exe` for those Python-read
variables; avoid ambiguous `/c/...` environment-variable values.

## 3. Start Desktop + Backend + local AI

In the activated terminal, from `finalbuild`:

```bash
export AI_CAR_BACKEND_HOST=0.0.0.0
export AI_CAR_BACKEND_PORT=8001

python -m apps.desktop.main --with-backend --local-ai
```

Keep Desktop and this terminal open. The launcher manages the local backend
and llama-server; closing Desktop stops the child processes it owns.
`--with-backend` selects the Desktop local SQLite database rather than requiring
an old configured PostgreSQL service. The API listens on 8001; the local AI
server normally listens on 8000. These are different services.

## 4. Verify Backend before connecting Android

In a second Git Bash terminal:

```bash
curl --fail --show-error --max-time 10 http://127.0.0.1:8001/health
```

Continue only after this returns JSON with `"status":"ok"`. A refused connection
here means the computer's backend is not listening; changing Android's address
will not start it. Check the first terminal and, if necessary:

```bash
tail -n 100 "$APPDATA/AI-Car-Scanner/backend.log"
```

Local AI can be checked independently with:

```bash
curl --fail --show-error --max-time 10 http://127.0.0.1:8000/health
```

## 5. Build, install and open Android on an emulator

Start an emulator in Android Studio Device Manager. Then in the second terminal:

```bash
cd ~/Desktop/AI-CAR-SCANER/git/finalbuild/apps/mobile-android

export ANDROID_HOME="$(cygpath -m "$LOCALAPPDATA/Android/Sdk")"
# Use an installed JDK 17; example when this is Android Studio's JBR version:
# export JAVA_HOME="C:/Program Files/Android/Android Studio/jbr"

./gradlew --version
./gradlew installDebug -PapiBaseUrl=http://10.0.2.2:8001/

ADB="$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"
"$ADB" devices
"$ADB" shell am start -n com.aicarscaner.mobile/.MainActivity
```

The Java version shown by Gradle must match the project's JDK 17 requirement.
Android Studio JBR versions vary; check rather than assuming the bundled JBR is
17. Set `JAVA_HOME` to an installed JDK 17 directory if needed.

In Android **Settings → Backend connection**, set:

```text
http://10.0.2.2:8001
```

Press **Apply and reopen**. A previously saved app URL takes precedence over the
Gradle build default; reinstalling with `-r` does not erase that saved value.
`10.0.2.2` is the emulator's route to the computer. The app connects to Backend;
it does not start a Python backend inside Android.

If emulator networking is blocked but the computer's health check succeeds:

```bash
"$ADB" reverse tcp:8001 tcp:8001
```

Then set the app URL to `http://127.0.0.1:8001` and apply/reopen. This alternative
requires the ADB connection to remain available.

For a physical phone over Wi-Fi, use the computer's LAN IPv4 address on the same
network, not `10.0.2.2` or the phone's own localhost.

## 6. Subsequent starts

For each new Git Bash terminal that runs Desktop:

```bash
cd ~/Desktop/AI-CAR-SCANER/git
source .venv/Scripts/activate
cd finalbuild
AI_CAR_BACKEND_HOST=0.0.0.0 python -m apps.desktop.main --with-backend --local-ai
```

For local packaged builds and required native toolchains, see
[the local build guide](docs/building/BUILD_ALL.md). iOS compilation requires
macOS/Xcode; it cannot be performed by the Windows setup above.
