"""Build orchestration contracts without invoking external SDKs or installers."""
from __future__ import annotations

from argparse import Namespace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import importlib.util

spec = importlib.util.spec_from_file_location("unified_native_build", Path(__file__).resolve().parents[1] / "scripts/build_all.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def arguments(tmp_path, **overrides):
    values = dict(targets=list(build.TARGETS), output=tmp_path / "artifacts", check=False,
                  skip_unavailable=False, with_tests=False, no_install=True)
    values.update(overrides)
    return Namespace(**values)


def summary(tmp_path):
    return json.loads(next((tmp_path / "artifacts").glob("*/build-summary.json")).read_text())


def fake_package(args, runner, work, output, tools):
    artifact = output / "package.zip"
    artifact.write_bytes(b"valid build output")
    return [artifact]


def test_one_failed_target_does_not_hide_successful_independent_builds(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "REPO", tmp_path)
    monkeypatch.setattr(build, "preflight", lambda target: [])
    def failed(*_args):
        raise build.BuildError("compiler exit 7")
    monkeypatch.setattr(build, "BUILDERS", {"desktop": fake_package, "android": failed, "ios": fake_package})
    assert build.execute(arguments(tmp_path)) == 1
    report = summary(tmp_path)
    assert report["status"] == "FAIL"
    assert report["targets"]["desktop"]["status"] == "PASS"
    assert report["targets"]["ios"]["status"] == "PASS"
    assert report["targets"]["android"]["artifacts"] == []
    assert "compiler exit 7" in report["targets"]["android"]["error"]


@pytest.mark.parametrize("allow_partial,expected_exit", [(False, 2), (True, 0)])
def test_unavailable_ios_is_explicit_and_never_reported_as_full_success(monkeypatch, tmp_path, allow_partial, expected_exit):
    monkeypatch.setattr(build, "REPO", tmp_path)
    monkeypatch.setattr(build, "preflight", lambda target: ["requires macOS/Xcode"] if target == "ios" else [])
    forbidden = Mock(side_effect=AssertionError("unsupported build must not run"))
    monkeypatch.setattr(build, "BUILDERS", {"desktop": fake_package, "android": fake_package, "ios": forbidden})
    assert build.execute(arguments(tmp_path, skip_unavailable=allow_partial)) == expected_exit
    result = summary(tmp_path)
    assert result["status"] == "PARTIAL"
    assert result["targets"]["ios"]["status"] == "UNAVAILABLE"
    forbidden.assert_not_called()


def test_no_available_target_fails_even_when_skip_is_requested(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "preflight", lambda target: ["missing SDK"])
    assert build.execute(arguments(tmp_path, skip_unavailable=True)) == 1
    assert summary(tmp_path)["status"] == "UNAVAILABLE"


def test_check_has_no_build_install_or_output_side_effects(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "preflight", lambda target: [])
    forbidden = Mock(side_effect=AssertionError("check must not execute builds"))
    monkeypatch.setattr(build, "BUILDERS", dict.fromkeys(build.TARGETS, forbidden))
    assert build.execute(arguments(tmp_path, check=True)) == 0
    assert not (tmp_path / "artifacts").exists()


def test_artifact_missing_after_successful_command_is_a_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "REPO", tmp_path)
    monkeypatch.setattr(build, "preflight", lambda target: [])
    monkeypatch.setattr(build, "BUILDERS", {"android": lambda *args: [tmp_path / "missing.apk"]})
    assert build.execute(arguments(tmp_path, targets=["android"])) == 1
    assert summary(tmp_path)["targets"]["android"]["status"] == "FAIL"


def test_artifact_hashes_match_downloadable_output_and_runs_are_isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "REPO", tmp_path)
    monkeypatch.setattr(build, "preflight", lambda target: [])
    monkeypatch.setattr(build, "BUILDERS", {"android": fake_package})
    for _ in range(2):
        assert build.execute(arguments(tmp_path, targets=["android"])) == 0
    reports = list((tmp_path / "artifacts").glob("*/build-summary.json"))
    assert len(reports) == 2
    for file in reports:
        report = json.loads(file.read_text())
        entry = report["targets"]["android"]["artifacts"][0]
        data = (file.parent / entry["path"]).read_bytes()
        assert entry["size_bytes"] == len(data)
        assert entry["sha256"] == hashlib.sha256(data).hexdigest()


def test_runner_preserves_nonzero_exit_and_captures_diagnostics(tmp_path):
    runner = build.Runner(tmp_path / "logs/command.log")
    import sys
    with pytest.raises(build.BuildError, match="exit 7"):
        runner.run([sys.executable, "-c", "print('compiler diagnostic'); raise SystemExit(7)"], cwd=tmp_path)
    assert "compiler diagnostic" in runner.log.read_text()


def test_ios_preflight_is_actionable_on_windows(monkeypatch):
    monkeypatch.setattr(build.platform, "system", lambda: "Windows")
    reasons = build.preflight("ios")
    assert "macOS" in reasons[0]
    assert "--ci" in reasons[0]


def test_android_sdk_reads_local_properties_without_changing_shell_home(monkeypatch, tmp_path):
    project = tmp_path / "project"
    (project / "apps/mobile-android").mkdir(parents=True)
    sdk = tmp_path / "sdk with spaces"
    sdk.mkdir()
    (project / "apps/mobile-android/local.properties").write_text(f"sdk.dir={sdk.as_posix()}\n")
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    monkeypatch.setattr(build, "PROJECT", project)
    assert build.android_sdk() == sdk


def test_ios_test_destination_uses_available_iphone_not_hardcoded_model(monkeypatch):
    data = {"devices": {"com.apple.CoreSimulator.SimRuntime.iOS-18-2": [
        {"name": "iPhone 16", "udid": "available-iphone", "isAvailable": True},
        {"name": "iPhone 15", "udid": "unavailable", "isAvailable": False},
        {"name": "iPad Pro", "udid": "ipad", "isAvailable": True}]}}
    monkeypatch.setattr(build.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(data)))
    assert build.simulator_destination() == "platform=iOS Simulator,id=available-iphone"


def test_ci_submission_does_not_report_a_completed_build(monkeypatch, capsys):
    monkeypatch.setattr(build, "executable", lambda name: "/tools/gh")
    command = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(build.subprocess, "run", command)
    assert build.main(["--ci", "--with-tests"]) == 0
    assert command.call_args.args[0] == ["gh", "workflow", "run", "build-all.yml", "--ref", "main", "-f", "run_tests=true"]
    assert "Builds are not complete yet" in capsys.readouterr().out


def test_ios_package_is_a_simulator_app_not_a_signed_ipa(monkeypatch, tmp_path):
    work = tmp_path / "work"
    output = tmp_path / "output"
    output.mkdir()
    app = work / "DerivedData/Build/Products/Debug-iphonesimulator/AICarScanner.app"
    app.mkdir(parents=True)
    (app / "Info.plist").write_text("simulator application metadata")
    runner = Mock()
    paths = build.build_ios(arguments(tmp_path), runner, work, output, tmp_path / "tools")
    import zipfile
    with zipfile.ZipFile(paths[0]) as archive:
        assert "AICarScanner.app/Info.plist" in archive.namelist()
    assert paths[0].name.endswith("iOS-Simulator.zip")
    commands = [call.args[0] for call in runner.run.call_args_list]
    assert any("CODE_SIGNING_ALLOWED=NO" in command and "iphonesimulator" in command for command in commands)
    assert not any("archive" in command or "-exportArchive" in command for command in commands)


def test_desktop_archive_keeps_gui_and_backend_together(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "REPO", tmp_path)
    monkeypatch.setattr(build, "desktop_python", lambda *args: Path("python.exe"))
    work = tmp_path / "work"
    dist = work / "dist"
    dist.mkdir(parents=True)
    for name in ("AICarScanner.exe", "backend_service.exe"):
        (dist / name).write_bytes(b"packaged executable fixture")
    output = tmp_path / "output"
    output.mkdir()
    paths = build.build_desktop(arguments(tmp_path), Mock(), work, output, tmp_path / "tools")
    import zipfile
    with zipfile.ZipFile(paths[0]) as archive:
        assert {"AICarScanner.exe", "backend_service.exe", "README.txt"}.issubset(archive.namelist())


def test_android_java_version_outside_gradle_support_is_rejected(monkeypatch, tmp_path):
    sdk = tmp_path / "sdk"
    (sdk / "platforms/android-36").mkdir(parents=True)
    (sdk / "platforms/android-36/android.jar").write_bytes(b"sdk")
    (sdk / "build-tools/35.0.0").mkdir(parents=True)
    monkeypatch.setattr(build, "android_sdk", lambda: sdk)
    monkeypatch.setattr(build, "java_executable", lambda: "java")
    monkeypatch.setattr(build.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout='', stderr='openjdk version "26.0.0"'))
    assert any("JDK 17" in reason for reason in build.preflight("android"))
