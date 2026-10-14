from __future__ import annotations

import builtins
import importlib.util
import io
import os
import runpy
from pathlib import Path
from urllib.error import URLError
from unittest.mock import Mock, call

import pytest

from apps.desktop import main


def test_json_health_handles_non_200_and_url_or_os_errors(monkeypatch):
    class Response:
        status = 503
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(main, "urlopen", lambda *_args, **_kwargs: Response())
    assert main._json_health("http://example.test/health") is False

    monkeypatch.setattr(main, "urlopen", Mock(side_effect=URLError("offline")))
    assert main._json_health("http://example.test/health") is False
    monkeypatch.setattr(main, "urlopen", Mock(side_effect=OSError("socket closed")))
    assert main._json_health("http://example.test/health") is False


def test_llama_server_resolution_and_model_override(monkeypatch, tmp_path):
    server = tmp_path / "llama-server"
    server.write_text("binary", encoding="utf-8")
    model = tmp_path / "model.gguf"

    monkeypatch.setenv("LOCAL_LLM_SERVER_PATH", str(server))
    monkeypatch.setattr(main.sys, "frozen", False, raising=False)
    assert main._resolve_llama_server() == server.resolve()

    monkeypatch.setenv("LOCAL_LLM_SERVER_PATH", str(tmp_path / "missing"))
    monkeypatch.setattr(main.shutil, "which", lambda _name: str(server))
    assert main._resolve_llama_server() == server.resolve()

    monkeypatch.setattr(main.shutil, "which", lambda _name: None)
    assert main._resolve_llama_server() is None

    monkeypatch.setenv("LOCAL_LLM_MODEL_PATH", str(model))
    assert main._resolve_model_path() == model.resolve()
    monkeypatch.delenv("LOCAL_LLM_MODEL_PATH")
    monkeypatch.setattr(main, "ROOT", tmp_path)
    monkeypatch.setattr(main, "LLM_MODEL", "default.gguf")
    assert main._resolve_model_path() == (tmp_path / "models" / "default.gguf").resolve()


def test_start_llama_server_respects_disable_health_missing_model_and_busy_port(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("AI_CAR_DISABLE_LLM_AUTOSTART", "yes")
    assert main.start_llama_server() is None

    monkeypatch.setenv("AI_CAR_DISABLE_LLM_AUTOSTART", "0")
    monkeypatch.setattr(main, "_llm_healthy", lambda: True)
    assert main.start_llama_server() is None

    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    monkeypatch.setattr(main, "_resolve_model_path", lambda: Path("/missing/model.gguf"))
    assert main.start_llama_server() is None
    assert "model not found" in capsys.readouterr().err

    model = tmp_path / "model-for-test.gguf"
    model.write_text("test model", encoding="utf-8")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: None)
    assert main.start_llama_server() is None
    assert "llama-server.exe not found" in capsys.readouterr().err

    monkeypatch.setattr(main, "_resolve_llama_server", lambda: Path("/fake/llama-server"))
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: True)
    assert main.start_llama_server() is None
    assert "port" in capsys.readouterr().err.lower()


def test_appdata_and_backend_log_helpers_create_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    log_path = main._appdata_log("custom.log")
    assert log_path.name == "custom.log"
    assert log_path.parent.is_dir()
    assert main._log_path().name == "backend.log"
    assert main._backend_log_path() == main._log_path()


def test_run_handles_local_llm_start_error_then_runs_ui_and_cleanup(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(main, "LOCAL_BACKEND", True)
    monkeypatch.setattr(main, "start_llama_server", Mock(side_effect=RuntimeError("LLM spawn failed")))
    monkeypatch.setattr(main, "start_backend", lambda: calls.append("backend-start"))
    monkeypatch.setattr(main, "stop_backend", lambda: calls.append("backend-stop"))
    monkeypatch.setattr(main, "stop_llama_server", lambda: calls.append("llm-stop"))
    monkeypatch.setattr("apps.desktop.ui.run", lambda: calls.append("ui"))

    main.run()

    assert calls == ["backend-start", "ui", "backend-stop", "llm-stop"]
    assert "Local LLM startup failed: LLM spawn failed" in capsys.readouterr().err


def test_health_helpers_use_the_configured_health_urls(monkeypatch):
    health = Mock(side_effect=[True, False])
    monkeypatch.setattr(main, "_json_health", health)

    assert main._backend_healthy() is True
    assert main._llm_healthy() is False
    assert health.call_args_list == [call(main.HEALTH_URL), call(main.LLM_HEALTH_URL)]


def test_frozen_module_bootstrap_resolves_bundle_and_skips_inaccessible_candidates(
    monkeypatch, tmp_path
):
    app_root = tmp_path / "installed"
    bundle_root = tmp_path / "bundle"
    app_root.mkdir()
    bundle_root.mkdir()
    executable = app_root / "AICarScanner.exe"

    monkeypatch.setattr(main.sys, "frozen", True, raising=False)
    monkeypatch.setattr(main.sys, "_MEIPASS", str(bundle_root), raising=False)
    monkeypatch.setattr(main.sys, "executable", str(executable))
    monkeypatch.setattr(
        main.sys,
        "path",
        [entry for entry in main.sys.path if entry != str(app_root.resolve())],
    )
    monkeypatch.delenv("LOCAL_LLM_SERVER_PATH", raising=False)

    spec = importlib.util.spec_from_file_location(
        "desktop_main_frozen_coverage", main.__file__
    )
    assert spec is not None and spec.loader is not None
    frozen_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen_main)

    assert frozen_main.ROOT == app_root.resolve()
    assert frozen_main.BUNDLE_ROOT == bundle_root.resolve()
    assert str(app_root.resolve()) in frozen_main.sys.path

    installed_server = app_root / "llama-server.exe"
    bundled_server = bundle_root / "llama-server.exe"
    installed_server.write_bytes(b"installed")
    bundled_server.write_bytes(b"bundle")
    monkeypatch.setattr(frozen_main.shutil, "which", lambda _name: None)

    assert frozen_main._resolve_llama_server() == installed_server.resolve()
    installed_server.unlink()
    assert frozen_main._resolve_llama_server() == bundled_server.resolve()

    bundled_server.unlink()
    inaccessible = app_root / "inaccessible-server"
    monkeypatch.setenv("LOCAL_LLM_SERVER_PATH", str(inaccessible))
    real_is_file = Path.is_file

    def is_file_with_permission_error(candidate):
        if candidate == inaccessible:
            raise OSError("permission denied")
        return real_is_file(candidate)

    monkeypatch.setattr(Path, "is_file", is_file_with_permission_error)
    assert frozen_main._resolve_llama_server() is None


def _prepare_llama_server_test(monkeypatch, tmp_path, process, health_checks, timeout=30):
    monkeypatch.setattr(main, "_llm_process", None)
    monkeypatch.setattr(main, "_llm_log", None)
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setenv("LOCAL_LLM_SERVER_NO_WEBUI", "true")
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")
    server = tmp_path / "llama-server.exe"
    server.write_bytes(b"test executable")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: server)
    monkeypatch.setattr(main, "_llm_healthy", Mock(side_effect=health_checks))
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main, "_appdata_log", lambda _name: tmp_path / "llama.log")
    monkeypatch.setattr(main, "_LLM_STARTUP_TIMEOUT", timeout)
    process.poll.return_value = None
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))
    return server


def test_llama_startup_adds_no_webui_and_waits_until_health_is_ready(
    monkeypatch, tmp_path
):
    process = Mock()
    _prepare_llama_server_test(
        monkeypatch, tmp_path, process, health_checks=[False, False, True]
    )
    sleep = Mock()
    monkeypatch.setattr(main.time, "sleep", sleep)

    assert main.start_llama_server(wait_for_ready=True) is process
    command = main.subprocess.Popen.call_args.args[0]
    assert "--no-webui" in command
    sleep.assert_called_once_with(0.25)
    main._close_llm_log()


def test_llama_startup_timeout_swallows_failure_of_both_cleanup_attempts(
    monkeypatch, tmp_path
):
    process = Mock()
    process.wait.side_effect = [
        RuntimeError("graceful wait failed"),
        RuntimeError("kill wait failed"),
    ]
    _prepare_llama_server_test(
        monkeypatch, tmp_path, process, health_checks=[False], timeout=0
    )

    assert main.start_llama_server(wait_for_ready=True) is None
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    assert main._llm_process is None
    assert main._llm_log is None


def test_frozen_backend_launches_bundled_executable_and_retries_health(
    monkeypatch, tmp_path
):
    app_root = tmp_path / "installed"
    app_root.mkdir()
    (app_root / "backend").mkdir()
    backend_exe = app_root / "backend_service.exe"
    backend_exe.write_bytes(b"fake executable")
    process = Mock()
    process.poll.return_value = None

    monkeypatch.setattr(main, "LOCAL_BACKEND", True)
    monkeypatch.setattr(main, "ROOT", app_root)
    monkeypatch.setattr(main, "BUNDLE_ROOT", app_root)
    monkeypatch.setattr(main.sys, "frozen", True, raising=False)
    monkeypatch.setattr(main, "_backend_process", None)
    monkeypatch.setattr(main, "_backend_log", None)
    monkeypatch.setattr(main, "_backend_log_path", lambda: tmp_path / "backend.log")
    monkeypatch.setattr(main, "_backend_healthy", Mock(side_effect=[False, False, True]))
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))
    sleep = Mock()
    monkeypatch.setattr(main.time, "sleep", sleep)

    assert main.start_backend() is process
    assert main.subprocess.Popen.call_args.args[0] == [str(backend_exe)]
    sleep.assert_called_once_with(0.25)
    main._close_backend_log()


def test_backend_timeout_swallows_failure_of_both_cleanup_attempts(
    monkeypatch, tmp_path
):
    (tmp_path / "backend").mkdir()
    process = Mock()
    process.poll.return_value = None
    process.wait.side_effect = [
        RuntimeError("graceful wait failed"),
        RuntimeError("kill wait failed"),
    ]

    monkeypatch.setattr(main, "LOCAL_BACKEND", True)
    monkeypatch.setattr(main, "ROOT", tmp_path)
    monkeypatch.setattr(main, "BUNDLE_ROOT", tmp_path)
    monkeypatch.setattr(main.sys, "frozen", False, raising=False)
    monkeypatch.setattr(main, "_backend_process", None)
    monkeypatch.setattr(main, "_backend_log", None)
    monkeypatch.setattr(main, "_backend_log_path", lambda: tmp_path / "backend.log")
    monkeypatch.setattr(main, "_backend_healthy", Mock(return_value=False))
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main, "_STARTUP_TIMEOUT", 0)
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))

    with pytest.raises(RuntimeError, match="did not become healthy"):
        main.start_backend()

    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    assert main._backend_process is None
    assert main._backend_log is None


def test_run_falls_back_to_absolute_ui_import_when_relative_import_fails(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(main, "LOCAL_BACKEND", False)
    monkeypatch.setattr(main, "start_backend", lambda: calls.append("backend-start"))
    monkeypatch.setattr(main, "stop_backend", lambda: calls.append("backend-stop"))
    monkeypatch.setattr(main, "stop_llama_server", lambda: calls.append("llm-stop"))
    monkeypatch.setattr("apps.desktop.ui.run", lambda: calls.append("ui"))
    original_import = builtins.__import__

    def fail_relative_ui_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "ui" and level == 1:
            raise ImportError("simulate running outside package context")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fail_relative_ui_import)
    main.run()
    assert calls == ["backend-start", "ui", "backend-stop", "llm-stop"]


def test_main_script_entrypoint_runs_without_starting_local_services(monkeypatch):
    calls = []
    monkeypatch.setenv("AI_CAR_BACKEND_URL", "https://remote.example.test")
    monkeypatch.setattr("apps.desktop.ui.run", lambda: calls.append("ui"))
    runpy.run_path(main.__file__, run_name="__main__")
    assert calls == ["ui"]
