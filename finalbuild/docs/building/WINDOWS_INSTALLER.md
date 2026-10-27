# Windows installer

By default the installer includes a pinned Git source snapshot and prepares Desktop +
Backend, and offers Local AI and Desktop shortcut checkboxes. Git, Android
Studio and a prebuilt Desktop ZIP are not required on the destination computer.
No CI/CD or automatic release publication is used.

## Build Setup.exe on Windows

Install [Inno Setup 6.3 or later](https://jrsoftware.org/isdl.php). You can use
Windows Package Manager:

```powershell
winget install --id JRSoftware.InnoSetup --exact --source winget
```

From the cloned repository root, after committing the desired source changes:

```bash
python installer.py
```

If the compiler is installed elsewhere:

```bash
python installer.py --iscc 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe'
```

Output:

```text
artifacts/windows-installer/dist/AI-Car-Scanner-Setup.exe
artifacts/windows-installer/dist/AI-Car-Scanner-Setup.exe.sha256
```

Distribute the Setup executable; recipients do not need the repository or
Python. The checksum identifies this exact installer. The build does not sign
or publish it. Production signing requires your own Windows code-signing
certificate; an unsigned download can display Windows SmartScreen.

The installer defaults to local `HEAD` and exports tracked files with
`git archive`. It includes neither Git history nor ignored/untracked files
such as local ENV overrides and virtual environments. The embedded snapshot
is verified against its manifest SHA-256 before extraction. Private GitHub
repositories do not require users to authenticate.

Use `--commit FULL_40_CHARACTER_SHA` for another commit available in the local
clone. The manifest records that exact source commit, not a moving branch.
For a smaller installer that fetches source at installation time, use
`python installer.py --online-only`. This mode requires the pinned commit to
be publicly downloadable; GitHub returns 404 for inaccessible/private sources.
Do not use online-only mode to distribute a private repository. `python installer.py --prepare-only` prepares an
inspectable payload on any OS, without claiming to compile a Windows executable.

## Installer appearance

The wizard uses the Desktop navy/neon-blue palette, Segoe UI typography,
existing abstract vehicle artwork, branded welcome/finish artwork and a
resizable window. The AI page, editable model path and review summary follow
the same colors; native Windows buttons/dialogs remain keyboard accessible.

## Installation choices

- **Local AI**, unchecked by default: downloads the verified llama.cpp CPU
  runtime and Qwen3 8B GGUF through the existing setup runner. Allow roughly
  5–6 GB additional download and enough disk/memory for the model. Without
  this checkbox the application and deterministic diagnostic workflows still
  install; local LLM startup is disabled.
- **Local model** on the AI page: unchecked downloads the verified default
  weights; checked enables a GGUF path field and Browse button. The file is
  checked before downloading the repository, passed to the existing runner's
  `--model` option and referenced without copying. The runtime may still need
  downloading. The last selected local model is remembered for repair.
- **Desktop shortcut**, checked by default: creates a shortcut using the
  existing application icon. A Start menu shortcut is always created.
- **Launch AI Car Scanner** on completion: starts Desktop, Backend and, when
  selected, local AI with no terminal window. Startup output is saved to disk.

Internet access is required for Python/PyPI and, when AI is selected,
Hugging Face/llama.cpp downloads. The default bundled source does not require
a GitHub source download; online-only mode does. A progress console displays the existing
runner's download/setup output. Failed setup returns to the wizard with an
error instead of claiming success; rerun Setup to retry. The AI downloader
retains resumable partial model downloads.

Python 3.12+ x64 is reused when available. If missing, Setup downloads the
latest stable Python 3.14 x64 installer linked by python.org, verifies its
Authenticode signature and Python Software Foundation publisher, and installs
it for the current user without adding it to PATH. This shared Python
installation remains after removing the application.

## Installed files and upgrades

Default location:

```text
%LOCALAPPDATA%\Programs\AI-Car-Scanner\
  installer\                 bootstrap, launcher helper, pinned manifest
  repo\                      GitHub snapshot, isolated .venv, runner state
  repo\finalbuild\models\    optional GGUF model
  environment.json           shared application ENV configuration
  logs\                      setup logs and desktop.log
  unins000.exe               Windows uninstaller
```

This is an application-managed snapshot without `.git` history, not a
modifiable development checkout. Keep development clones separately. Setup
refuses to overwrite an unrelated nonempty folder or linked checkout.

Close Desktop and its Backend/AI processes before upgrading or uninstalling;
Setup checks its own installation paths rather than killing unrelated Python
processes. Run a newer Setup.exe in the same folder to upgrade, or rerun the
same installer to change the AI/shortcut choices. Snapshot updates remove
obsolete source files and preserve the venv, downloaded models and runner
state until setup reconfigures them. Unchecking Local AI disables startup and
keeps previously downloaded weights for reuse; uninstall removes those files.

## Shared global settings

Setup creates `environment.json` beside the installed `repo` directory.
Desktop and Backend read it automatically when launched from shortcuts.
Edit ports, context, threads or other ENV options there and restart the app.
[JSON format, precedence and development overrides](ENVIRONMENT_CONFIG.md).
For scripted installs, select the `localai` task and pass
`/LOCALMODEL="C:\Models\model.gguf"` to use existing weights.

## Uninstall and troubleshooting

Use Windows **Settings → Apps → Installed apps → AI Car Scanner → Uninstall**,
the Start menu uninstall entry, or `unins000.exe`.

Removal deletes the managed source snapshot, virtual environment, downloaded
AI/cache files and shortcuts. Diagnostic/user data under
`%APPDATA%\AI-Car-Scanner` is retained. Python is not removed because other
applications may use it.

Setup displays its specific failure text inside the wizard. Early bootstrap
failures also persist under `%LOCALAPPDATA%\AI-Car-Scanner\installer-logs`
(transcripts and `last-error.txt`), including failures before Python starts.
Inspect `logs\setup-*.log`, `logs\bootstrap-errors.log` and
`logs\desktop.log` for application failures. Inno Setup also writes its own
Setup log to the Windows temporary folder. Python prerequisite failures appear
in the progress console and Setup log. There is no need to delete or reclone
your development repository to use this installer.

## Validation limits

Installer helper tests exercise real setup subprocesses with fixture snapshots,
AI selection, retry, safe extraction, ownership checks, upgrades and launch
error handling. The payload can be prepared on Linux. Windows PowerShell,
Inno compilation, shortcut registration and Apps/Uninstall behavior require a
Windows smoke test; cross-platform tests do not certify those OS integrations.
