from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from apps.desktop import main


@pytest.fixture(autouse=True)
def isolate_process_state(monkeypatch):
    monkeypatch.setattr(main, "_backend_process", None)
    monkeypatch.setattr(main, "_llm_process", None)
    monkeypatch.setattr(main, "_backend_log", None)
    monkeypatch.setattr(main, "_llm_log", None)


def _prepare_local_backend(monkeypatch, tmp_path, popen=None):
    monkeypatch.setattr(main, "LOCAL_BACKEND", True)
    monkeypatch.setattr(main, "ROOT", tmp_path)
    monkeypatch.setattr(main, "BUNDLE_ROOT", tmp_path)
    (tmp_path / "backend").mkdir(exist_ok=True)
    log_path = tmp_path / "backend.log"
    monkeypatch.setattr(main, "_backend_log_path", lambda: log_path)
    monkeypatch.setattr(main, "_backend_healthy", Mock(side_effect=[False, True]))
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    process = popen or Mock()
    process.poll.return_value = None
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))
    return process, log_path


def test_start_backend_skips_remote_backend(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_BACKEND", False)
    monkeypatch.setattr(main, "_backend_healthy", Mock(side_effect=AssertionError("should not probe")))
    assert main.start_backend() is None
    main._backend_healthy.assert_not_called()


def test_start_backend_skips_when_health_check_passes(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_BACKEND", True)
    monkeypatch.setattr(main, "_backend_healthy", lambda: True)
    monkeypatch.setattr(main.subprocess, "Popen", Mock(side_effect=AssertionError("should not spawn")))
    assert main.start_backend() is None


def test_start_backend_reports_unhealthy_port_conflict(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_BACKEND", True)
    monkeypatch.setattr(main, "_backend_healthy", lambda: False)
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: True)
    with pytest.raises(RuntimeError, match="already in use"):
        main.start_backend()


def test_start_backend_starts_source_mode_and_waits_for_health(monkeypatch, tmp_path):
    process, log_path = _prepare_local_backend(monkeypatch, tmp_path)
    result = main.start_backend()
    assert result is process
    call_args, kwargs = main.subprocess.Popen.call_args
    assert call_args[0][1:] == ["-m", "apps.desktop.backend_worker"]
    assert kwargs["cwd"] == str(tmp_path)
    assert kwargs["stdout"] is not None
    assert log_path.exists()
    assert main._backend_process is process
    main._close_backend_log()


def test_start_backend_wraps_uvicorn_missing_from_environment(monkeypatch, tmp_path):
    _prepare_local_backend(monkeypatch, tmp_path)
    main.subprocess.Popen.side_effect = FileNotFoundError("uvicorn not found")
    with pytest.raises(RuntimeError, match="uvicorn is not installed"):
        main.start_backend()
    assert main._backend_log is None


def test_start_backend_wraps_other_process_creation_errors(monkeypatch, tmp_path):
    _prepare_local_backend(monkeypatch, tmp_path)
    main.subprocess.Popen.side_effect = OSError("access denied")
    with pytest.raises(RuntimeError, match="Could not start backend process: access denied"):
        main.start_backend()
    assert main._backend_log is None


def test_start_backend_reports_frozen_build_without_bundled_service(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "LOCAL_BACKEND", True)
    monkeypatch.setattr(main, "ROOT", tmp_path)
    monkeypatch.setattr(main, "BUNDLE_ROOT", tmp_path)
    monkeypatch.setattr(main.sys, "frozen", True, raising=False)
    monkeypatch.setattr(main, "_backend_healthy", lambda: False)
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main, "_backend_log_path", lambda: tmp_path / "backend.log")
    with pytest.raises(RuntimeError, match="backend_service.exe was not found"):
        main.start_backend()
    assert main._backend_log is None


def test_start_backend_reports_process_exit_during_startup(monkeypatch, tmp_path):
    process = Mock()
    process.poll.return_value = 2
    process.returncode = 2
    _prepare_local_backend(monkeypatch, tmp_path, popen=process)
    # The helper initializes a still-running default process; override it
    # after setup so this scenario models an immediate child-process exit.
    process.poll.return_value = 2
    monkeypatch.setattr(main, "_backend_healthy", Mock(return_value=False))
    with pytest.raises(RuntimeError, match="exited during startup with code 2"):
        main.start_backend()
    assert main._backend_process is None
    assert main._backend_log is None


def test_start_backend_times_out_and_terminates_process(monkeypatch, tmp_path):
    process = Mock()
    process.poll.return_value = None
    _prepare_local_backend(monkeypatch, tmp_path, popen=process)
    monkeypatch.setattr(main, "_backend_healthy", Mock(return_value=False))
    monkeypatch.setattr(main, "_STARTUP_TIMEOUT", 0)
    with pytest.raises(RuntimeError, match="did not become healthy"):
        main.start_backend()
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=2)
    assert main._backend_process is None
    assert main._backend_log is None


def test_stop_backend_terminates_running_process_and_closes_log(monkeypatch, tmp_path):
    process = Mock()
    process.poll.return_value = None
    log = (tmp_path / "backend.log").open("w", encoding="utf-8")
    monkeypatch.setattr(main, "_backend_process", process)
    monkeypatch.setattr(main, "_backend_log", log)
    main.stop_backend()
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)
    assert main._backend_process is None
    assert log.closed
    assert main._backend_log is None


def test_stop_backend_kills_process_when_graceful_stop_times_out(monkeypatch):
    process = Mock()
    process.poll.return_value = None
    process.wait.side_effect = [subprocess.TimeoutExpired("backend", 5), None]
    monkeypatch.setattr(main, "_backend_process", process)
    main.stop_backend()
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2


def test_stop_backend_does_not_signal_already_exited_process(monkeypatch):
    process = Mock()
    process.poll.return_value = 0
    monkeypatch.setattr(main, "_backend_process", process)
    main.stop_backend()
    process.terminate.assert_not_called()
    assert main._backend_process is None


def test_start_llama_server_skips_missing_executable(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    model = tmp_path / "model.gguf"
    model.write_bytes(b"fake")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: None)
    assert main.start_llama_server() is None
    assert "llama-server.exe not found" in capsys.readouterr().err


def test_start_llama_server_skips_busy_unhealthy_port(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    model = tmp_path / "model.gguf"
    model.write_bytes(b"fake")
    server = tmp_path / "llama-server.exe"
    server.write_bytes(b"fake")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: server)
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: True)
    assert main.start_llama_server() is None
    stderr = capsys.readouterr().err
    assert "port" in stderr and "busy" in stderr


def test_start_llama_server_reports_spawn_error_and_closes_log(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")
    server = tmp_path / "llama-server"
    server.write_bytes(b"binary")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: server)
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main, "_appdata_log", lambda _name: tmp_path / "llama.log")
    monkeypatch.setattr(main.subprocess, "Popen", Mock(side_effect=OSError("cannot execute")))
    assert main.start_llama_server() is None
    assert main._llm_log is None


def test_start_llama_server_returns_process_when_health_arrives(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", Mock(side_effect=[False, True]))
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")
    server = tmp_path / "llama-server"
    server.write_bytes(b"binary")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: server)
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main, "_appdata_log", lambda _name: tmp_path / "llama.log")
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))
    result = main.start_llama_server(wait_for_ready=True)
    assert result is process
    main._close_llm_log()


def test_start_llama_server_reports_early_exit_and_closes_log(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")
    server = tmp_path / "llama-server"
    server.write_bytes(b"binary")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: server)
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main, "_appdata_log", lambda _name: tmp_path / "llama.log")
    process = Mock()
    process.poll.return_value = 7
    process.returncode = 7
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))
    assert main.start_llama_server(wait_for_ready=True) is None
    assert main._llm_process is None
    assert main._llm_log is None
    assert "exited with code 7" in capsys.readouterr().err


def test_start_llama_server_times_out_and_terminates_process(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    monkeypatch.setattr(main, "_LLM_STARTUP_TIMEOUT", 0)
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")
    server = tmp_path / "llama-server"
    server.write_bytes(b"binary")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: server)
    monkeypatch.setattr(main, "_is_port_open", lambda *_args: False)
    monkeypatch.setattr(main, "_appdata_log", lambda _name: tmp_path / "llama.log")
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))
    assert main.start_llama_server(wait_for_ready=True) is None
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=2)
    assert main._llm_process is None
    assert main._llm_log is None
    assert "did not become healthy" in capsys.readouterr().err


def test_stop_llama_server_kills_after_timeout_and_cleans_log(monkeypatch, tmp_path):
    process = Mock()
    process.poll.return_value = None
    process.wait.side_effect = [subprocess.TimeoutExpired("llama", 5), None]
    log = (tmp_path / "llama.log").open("w", encoding="utf-8")
    monkeypatch.setattr(main, "_llm_process", process)
    monkeypatch.setattr(main, "_llm_log", log)
    main.stop_llama_server()
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert log.closed
    assert main._llm_process is None
    assert main._llm_log is None


def test_stop_llama_server_closes_log_even_without_process(monkeypatch, tmp_path):
    log = (tmp_path / "llama.log").open("w", encoding="utf-8")
    monkeypatch.setattr(main, "_llm_process", None)
    monkeypatch.setattr(main, "_llm_log", log)
    main.stop_llama_server()
    assert log.closed
    assert main._llm_log is None


def test_run_always_stops_services_when_ui_returns(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "LOCAL_BACKEND", False)
    monkeypatch.setattr(main, "start_backend", lambda: calls.append("start backend"))
    monkeypatch.setattr(main, "stop_backend", lambda: calls.append("stop backend"))
    monkeypatch.setattr(main, "stop_llama_server", lambda: calls.append("stop llm"))
    monkeypatch.setattr(main, "start_llama_server", lambda **_kwargs: calls.append("start llm"))
    monkeypatch.setattr("apps.desktop.ui.run", lambda: calls.append("run ui"))
    main.run()
    assert calls == ["start backend", "run ui", "stop backend", "stop llm"]


def test_run_reports_backend_start_error_after_ui_and_cleanup(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(main, "LOCAL_BACKEND", False)
    monkeypatch.setattr(main, "start_backend", Mock(side_effect=RuntimeError("bind failed")))
    monkeypatch.setattr(main, "stop_backend", lambda: calls.append("stop backend"))
    monkeypatch.setattr(main, "stop_llama_server", lambda: calls.append("stop llm"))
    monkeypatch.setattr("apps.desktop.ui.run", lambda: calls.append("run ui"))
    with pytest.raises(SystemExit) as error:
        main.run()
    assert error.value.code == 1
    assert calls == ["run ui", "stop backend", "stop llm"]
    assert "Backend startup failed: bind failed" in capsys.readouterr().err

@pytest.mark.parametrize('configured,force_local,expect_local', [
    (None, False, True),
    ('postgresql+psycopg://localhost/diagnostic', False, False),
    ('postgresql+psycopg://localhost/diagnostic', True, True),
])
def test_launcher_storage_selection_is_explicit(monkeypatch, tmp_path, configured, force_local, expect_local):
    _prepare_local_backend(monkeypatch, tmp_path)
    if configured is None:
        monkeypatch.delenv('DATABASE_URL', raising=False)
    else:
        monkeypatch.setenv('DATABASE_URL', configured)
    monkeypatch.setenv('AI_CAR_USE_LOCAL_DATABASE', '1' if force_local else '0')
    # A stale inherited internal marker must not seed a configured database.
    monkeypatch.setenv('AI_CAR_DESKTOP_LOCAL_DB', '1')
    try:
        main.start_backend()
        env = main.subprocess.Popen.call_args.kwargs['env']
        assert (env.get('AI_CAR_DESKTOP_LOCAL_DB') == '1') is expect_local
        if expect_local:
            assert env['DATABASE_URL'].startswith('sqlite:///')
            assert env['DATABASE_URL'].endswith('/diagnostic.sqlite')
        else:
            assert env['DATABASE_URL'] == configured
        assert env['PYTHONUNBUFFERED'] == '1'
    finally:
        main._close_backend_log()
