"""Build native applications with explicit prerequisites, logs and artifacts.

Examples from the repository root:
  python build.py --check
  python build.py --targets desktop android
  python build.py --skip-unavailable

Windows EXE packaging requires Windows; iOS requires macOS/Xcode.
Run the same local entrypoint on each required operating system.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import threading
import subprocess
import sys
import venv

REPO = Path(__file__).resolve().parents[2]
PROJECT = REPO / "finalbuild"
TARGETS = ("desktop", "android", "ios")


class BuildError(RuntimeError):
    pass


def executable(name: str) -> str | None:
    return shutil.which(name)


def android_sdk() -> Path | None:
    candidates = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT")]
    local = PROJECT / "apps/mobile-android/local.properties"
    if local.is_file():
        for line in local.read_text(encoding="utf-8").splitlines():
            if line.startswith("sdk.dir="):
                candidates.append(line.partition("=")[2].replace("\\:", ":").replace("\\\\", "\\"))
    candidates += [str(Path.home() / "Android/Sdk"), str(Path.home() / "Library/Android/sdk")]
    if os.environ.get("LOCALAPPDATA"):
        candidates.append(str(Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk"))
    return next((Path(p).expanduser().resolve() for p in candidates if p and Path(p).expanduser().is_dir()), None)


def java_executable() -> str | None:
    if os.environ.get("JAVA_HOME"):
        candidate = Path(os.environ["JAVA_HOME"]) / "bin" / ("java.exe" if platform.system() == "Windows" else "java")
        if candidate.is_file():
            return str(candidate)
    return executable("java")


def preflight(target: str) -> list[str]:
    problems = []
    if target == "desktop":
        if platform.system() != "Windows":
            problems.append("Desktop .exe packaging requires Windows; run this builder on Windows.")
        if sys.version_info < (3, 12):
            problems.append("Desktop requires Python 3.12+ (Windows Python 3.14 x64 recommended).")
        if sys.maxsize <= 2**32:
            problems.append("Desktop requires a 64-bit Python installation.")
    elif target == "android":
        java = java_executable()
        if not java:
            problems.append("Install JDK 17 and set JAVA_HOME (or put java on PATH).")
        else:
            try:
                version = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=15)
                match = re.search(r'version\s+"(\d+)', version.stdout + version.stderr)
                if version.returncode or match is None or not 17 <= int(match[1]) <= 23:
                    problems.append("This Gradle version supports JDK 17–23; set JAVA_HOME to JDK 17 or 21.")
            except (OSError, subprocess.TimeoutExpired) as error:
                problems.append(f"Cannot run Java: {error}")
        sdk = android_sdk()
        if sdk is None:
            problems.append("Install Android Studio SDK; set ANDROID_HOME or ANDROID_SDK_ROOT.")
        else:
            if not (sdk / "platforms/android-36/android.jar").is_file():
                problems.append("Install SDK platform android-36 using Android Studio SDK Manager.")
            if not (sdk / "build-tools").is_dir() or not any((sdk / "build-tools").iterdir()):
                problems.append("Install Android SDK build-tools (35.0.0 or newer).")
        if platform.system() != "Windows" and executable("bash") is None:
            problems.append("Install bash to run the bundled Gradle wrapper.")
    elif target == "ios":
        if platform.system() != "Darwin":
            return ["iOS requires macOS with Xcode; run this builder on a Mac."]
        for tool in ("xcodebuild", "xcrun", "xcodegen"):
            if executable(tool) is None:
                problems.append(f"Install {tool}; XcodeGen can be installed with: brew install xcodegen")
        if not problems:
            try:
                result = subprocess.run(["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"], capture_output=True, text=True, timeout=30)
                if result.returncode:
                    problems.append("Select full Xcode with xcode-select, accept its license and install the iOS Simulator SDK.")
            except (OSError, subprocess.TimeoutExpired) as error:
                problems.append(f"Cannot query the iOS Simulator SDK: {error}")
    else:
        raise ValueError(f"Unknown build target: {target}")
    return problems


class Runner:
    def __init__(self, log: Path):
        self.log = log
        log.parent.mkdir(parents=True, exist_ok=True)

    def run(self, command: list[str], *, cwd: Path = PROJECT, env: dict | None = None, timeout: int = 1800) -> None:
        command = [str(item) for item in command]
        env = dict(os.environ if env is None else env)
        env["PYTHONUNBUFFERED"] = "1"
        print(f"[BUILD] {command[0]} {' '.join(command[1:3])} ...", flush=True)
        with self.log.open("a", encoding="utf-8") as log:
            log.write("\nCOMMAND: " + subprocess.list2cmdline(command) + "\n")
            log.flush()
            # Keep the complete log and show live output while long tools run.
            offset = log.tell()
            done = threading.Event()
            def stream():
                with self.log.open(encoding="utf-8", errors="replace") as source:
                    source.seek(offset)
                    while True:
                        chunk = source.read()
                        if chunk:
                            print(chunk, end="", flush=True)
                        if done.wait(0.2):
                            print(source.read(), end="", flush=True)
                            return
            watcher = threading.Thread(target=stream, daemon=True)
            watcher.start()
            options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
            process = None
            try:
                process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, **options)
                process.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                if process is not None:
                    if os.name == "nt":
                        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                    else:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    process.wait(timeout=15)
                if isinstance(error, KeyboardInterrupt):
                    raise
                raise BuildError(f"Command timed out after {timeout}s; see {self.log}") from error
            finally:
                done.set()
                watcher.join(timeout=5)
        if process.returncode:
            raise BuildError(f"Command failed (exit {process.returncode}); see {self.log}")


def require_file(path: Path) -> Path:
    if not path.is_file() or path.stat().st_size == 0:
        raise BuildError(f"Build command returned but required artifact is missing/empty: {path}")
    return path


def desktop_python(args, runner: Runner, tools: Path) -> Path:
    if args.no_install:
        runner.run([sys.executable, "-c", "import PyInstaller, PySide6, PIL"])
        return Path(sys.executable)
    environment = tools / "desktop-venv"
    python = environment / "Scripts/python.exe"
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(environment)
    requirements = ["-r", "requirements.txt"]
    if args.with_tests:
        requirements += ["-r", "backend/requirements-dev.txt", "-r", "apps/desktop/requirements-dev.txt"]
    runner.run([str(python), "-m", "pip", "install", *requirements])
    return python


def build_desktop(args, runner: Runner, work: Path, output: Path, tools: Path) -> list[Path]:
    python = desktop_python(args, runner, tools)
    env = os.environ.copy()
    env.update({"AI_CAR_DISABLE_LLM_AUTOSTART": "1", "QT_QPA_PLATFORM": "offscreen"})
    if args.with_tests:
        runner.run([str(python), "scripts/run_desktop_tests.py", "--min-core-coverage", "90",
                    "--reports-dir", str(output / "test-reports")], env=env)
    icons = work / "icons"
    source = PROJECT / "assets/AI-Car-Scanner-master.png"
    # Honor edited local artwork; never regenerate tracked assets in-place.
    if executable("git") and (REPO / ".git").exists():
        edited = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "assets/AI-Car-Scanner-mobile.png"], cwd=PROJECT)
        if edited.returncode == 1:
            source = PROJECT / "assets/AI-Car-Scanner-mobile.png"
    runner.run([str(python), "apps/desktop/stage_windows_icons.py", "--source", str(source), "--output-dir", str(icons)], env=env)
    env["AI_CAR_ICON_STAGE_DIR"] = str(icons)
    dist = work / "dist"
    for spec, folder in [("backend_service.spec", "backend"), ("AICarScanner.spec", "gui")]:
        runner.run([str(python), "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(dist), "--workpath", str(work / folder), "apps/desktop/specs/" + spec], env=env)
    for filename in ("AICarScanner.exe", "backend_service.exe"):
        require_file(dist / filename)
    (dist / "README.txt").write_text(
        "AI CAR SCANNER — Windows Desktop\n\nExtract this entire ZIP. Keep both executables together.\n"
        "Run: AICarScanner.exe --with-backend\n"
        "Local SQLite storage is prepared by the launcher.\n"
        "Local AI model/server binaries are configured separately and are not downloaded by this builder.\n",
        encoding="utf-8",
    )
    archive = Path(shutil.make_archive(str(output / "AI-Car-Scanner-Windows"), "zip", dist))
    return [require_file(archive)]


def build_android(args, runner: Runner, work: Path, output: Path, tools: Path) -> list[Path]:
    project = PROJECT / "apps/mobile-android"
    wrapper = project / ("gradlew.bat" if platform.system() == "Windows" else "gradlew")
    command = ["cmd.exe", "/d", "/c", str(wrapper)] if platform.system() == "Windows" else ["bash", str(wrapper)]
    tasks = [":app:assembleDebug"]
    if args.with_tests:
        tasks += [":app:testDebugUnitTest", ":app:lintDebug"]
    env = os.environ.copy()
    sdk = android_sdk()
    if sdk:
        env["ANDROID_HOME"] = str(sdk)
        env["ANDROID_SDK_ROOT"] = str(sdk)
    env.setdefault("GRADLE_USER_HOME", str(tools / "gradle"))
    api_url = getattr(args, "android_api_url", None)
    properties = [f"-PapiBaseUrl={api_url}"] if api_url else []
    runner.run(command + tasks + properties + ["--no-daemon", "--console=plain"], cwd=project, env=env)
    source = require_file(project / "app/build/outputs/apk/debug/app-debug.apk")
    target = output / "AI-Car-Scanner-Android-debug.apk"
    shutil.copy2(source, target)
    return [require_file(target)]


def simulator_destination() -> str:
    result = subprocess.run(["xcrun", "simctl", "list", "devices", "available", "--json"], capture_output=True, text=True, check=True, timeout=30)
    candidates = []
    for runtime, devices in json.loads(result.stdout).get("devices", {}).items():
        if ".iOS-" not in runtime:
            continue
        version = tuple(int(value) for value in re.findall(r"\d+", runtime))
        for device in devices:
            if device.get("isAvailable") and "iPhone" in device.get("name", "") and device.get("udid"):
                candidates.append((version, device["udid"]))
    if not candidates:
        raise BuildError("iOS tests require an installed iPhone simulator runtime; install one in Xcode Settings > Platforms.")
    return "platform=iOS Simulator,id=" + max(candidates)[1]


def build_ios(args, runner: Runner, work: Path, output: Path, tools: Path) -> list[Path]:
    project = PROJECT / "apps/mobile-ios"
    runner.run(["xcodegen", "generate", "--spec", "project.yml"], cwd=project)
    common = ["xcodebuild", "-project", "AICarScanner.xcodeproj", "-scheme", "AICarScanner", "-configuration", "Debug", "-derivedDataPath", str(work / "DerivedData"), "CODE_SIGNING_ALLOWED=NO"]
    runner.run(common + ["-sdk", "iphonesimulator", "-destination", "generic/platform=iOS Simulator", "build"], cwd=project)
    if args.with_tests:
        runner.run(common + ["-destination", simulator_destination(), "-enableCodeCoverage", "YES", "-resultBundlePath", str(output / "TestResults.xcresult"), "test"], cwd=project)
    application = work / "DerivedData/Build/Products/Debug-iphonesimulator/AICarScanner.app"
    require_file(application / "Info.plist")
    archive = Path(shutil.make_archive(str(output / "AI-Car-Scanner-iOS-Simulator"), "zip", application.parent, application.name))
    return [require_file(archive)]


BUILDERS = {"desktop": build_desktop, "android": build_android, "ios": build_ios}


def artifact_record(path: Path, run: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path.relative_to(run)), "size_bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def execute(args) -> int:
    plans = {target: preflight(target) for target in args.targets}
    for target, problems in plans.items():
        print(f"[{target.upper()}] " + ("READY" if not problems else "UNAVAILABLE: " + "; ".join(problems)), flush=True)
    if args.check:
        return 2 if any(plans.values()) else 0
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run = args.output.resolve() / stamp
    run.mkdir(parents=True)
    tools = REPO / ".build-tools"
    summary = {"status": "RUNNING", "host": platform.system(), "requested_targets": args.targets, "with_tests": args.with_tests, "targets": {}}
    report = run / "build-summary.json"

    def save():
        report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    save()
    for target, problems in plans.items():
        if problems:
            summary["targets"][target] = {"status": "UNAVAILABLE", "reasons": problems, "artifacts": []}
            save()
            continue
        output = run / target
        output.mkdir()
        runner = Runner(output / "build.log")
        work = tools / "work" / stamp / target
        work.mkdir(parents=True)
        try:
            artifacts = BUILDERS[target](args, runner, work, output, tools)
            if not artifacts:
                raise BuildError("No artifacts produced")
            records = [artifact_record(require_file(path), run) for path in artifacts]
            entry = {"status": "PASS", "artifacts": records}
        except KeyboardInterrupt:
            summary["targets"][target] = {"status": "CANCELLED", "artifacts": [], "log": str(runner.log.relative_to(run))}
            for pending in args.targets:
                summary["targets"].setdefault(pending, {"status": "NOT_RUN", "artifacts": []})
            summary["status"] = "CANCELLED"
            save()
            print(f"\n[SUMMARY] CANCELLED — {report}", flush=True)
            return 130
        except Exception as error:
            entry = {"status": "FAIL", "error": str(error), "artifacts": []}
        entry["log"] = str(runner.log.relative_to(run))
        summary["targets"][target] = entry
        print(f"[{target.upper()}] {entry['status']}" + (f": {entry['error']}" if entry.get("error") else ""), flush=True)
        save()
    statuses = [result["status"] for result in summary["targets"].values()]
    if "FAIL" in statuses:
        summary["status"] = "FAIL"
    elif "UNAVAILABLE" in statuses:
        summary["status"] = "PARTIAL" if "PASS" in statuses else "UNAVAILABLE"
    else:
        summary["status"] = "PASS"
    save()
    print(f"[SUMMARY] {summary['status']} — {report}", flush=True)
    if "FAIL" in statuses or "PASS" not in statuses:
        return 1
    if "UNAVAILABLE" in statuses and not args.skip_unavailable:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--targets", nargs="+", choices=TARGETS, default=list(TARGETS))
    parser.add_argument("--output", type=Path, default=REPO / "artifacts", help="Artifact base directory; each run has its own timestamped folder")
    parser.add_argument("--check", action="store_true", help="Check toolchains only; do not install, build or write outputs")
    parser.add_argument("--skip-unavailable", action="store_true", help="Allow a partial local build; unavailable targets remain explicitly reported")
    parser.add_argument("--with-tests", action="store_true", help="Run Desktop regression, Android JVM/lint, and iOS XCTest before reporting success")
    parser.add_argument("--no-install", action="store_true", help="Use current Python's existing Desktop dependencies instead of creating/updating an isolated environment")
    parser.add_argument("--android-api-url", help="Backend URL embedded in the Android app, e.g. http://10.0.2.2:8001/")
    args = parser.parse_args(argv)
    args.targets = list(dict.fromkeys(args.targets))
    if args.android_api_url:
        from urllib.parse import urlsplit
        try:
            url = urlsplit(args.android_api_url)
            if url.port == 0:
                raise ValueError("port zero")
        except ValueError:
            parser.error("--android-api-url has an invalid host or port")
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
            parser.error("--android-api-url requires an HTTP(S) backend URL without credentials/query/fragment")
    try:
        return execute(args)
    except KeyboardInterrupt:
        print("Build cancelled.", file=sys.stderr)
        return 130
    except (OSError, subprocess.SubprocessError) as error:
        print(f"Build setup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
