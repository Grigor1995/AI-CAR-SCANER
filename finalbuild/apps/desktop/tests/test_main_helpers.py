from __future__ import annotations

from urllib.error import URLError
from unittest.mock import MagicMock, Mock


from apps.desktop import main


def test_is_port_open_closes_socket(monkeypatch):
    class FakeSocket:
        closed = False

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.closed = True

        def settimeout(self, value):
            assert value == 0.25

        def connect_ex(self, address):
            assert address == ("127.0.0.1", 8001)
            return 0

    sock = FakeSocket()
    monkeypatch.setattr(main.socket, "socket", lambda *_: sock)
    assert main._is_port_open("127.0.0.1", 8001) is True
    assert sock.closed is True


def test_json_health_returns_status_and_handles_network_errors(monkeypatch):
    response = MagicMock()
    response.status = 200
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(main, "urlopen", lambda *args, **kwargs: response)
    assert main._json_health("http://backend.test/health") is True

    response.status = 503
    assert main._json_health("http://backend.test/health") is False
    monkeypatch.setattr(main, "urlopen", Mock(side_effect=URLError("offline")))
    assert main._json_health("http://backend.test/health") is False


def test_appdata_log_creates_app_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = main._appdata_log("backend.log")
    assert path == tmp_path / "AI-Car-Scanner" / "backend.log"
    assert path.parent.is_dir()


def test_resolve_model_path_honors_environment_override(tmp_path, monkeypatch):
    configured = tmp_path / "model.gguf"
    monkeypatch.setenv("LOCAL_LLM_MODEL_PATH", str(configured))
    assert main._resolve_model_path() == configured.resolve()


def test_resolve_llama_server_uses_configured_existing_path(tmp_path, monkeypatch):
    executable = tmp_path / "llama-server"
    executable.write_text("fake executable", encoding="utf-8")
    monkeypatch.setenv("LOCAL_LLM_SERVER_PATH", str(executable))
    monkeypatch.setattr(main.shutil, "which", lambda _: None)
    assert main._resolve_llama_server() == executable.resolve()


def test_resolve_llama_server_ignores_missing_configured_path(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_SERVER_PATH", str(tmp_path / "missing"))
    monkeypatch.setattr(main.shutil, "which", lambda _: None)
    assert main._resolve_llama_server() is None


def test_start_llama_server_can_return_while_model_loads(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", Mock(return_value=False))
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")
    server = tmp_path / "llama-server.exe"
    server.write_bytes(b"executable")
    monkeypatch.setattr(main, "_resolve_model_path", lambda: model)
    monkeypatch.setattr(main, "_resolve_llama_server", lambda: server)
    monkeypatch.setattr(main, "_is_port_open", lambda *_: False)
    monkeypatch.setattr(main, "_appdata_log", lambda name: tmp_path / name)
    monkeypatch.setattr(main, "_llm_process", None)
    monkeypatch.setattr(main, "_llm_log", None)
    process = Mock()
    monkeypatch.setattr(main.subprocess, "Popen", Mock(return_value=process))

    assert main.start_llama_server(wait_for_ready=False) is process
    assert main._llm_healthy.call_count == 1
    main._llm_log.close()
    main._llm_log = None


def test_start_llama_server_respects_disabled_flag(monkeypatch):
    monkeypatch.setenv("AI_CAR_DISABLE_LLM_AUTOSTART", "true")
    healthy = Mock(side_effect=AssertionError("health check should not run"))
    monkeypatch.setattr(main, "_llm_healthy", healthy)
    assert main.start_llama_server() is None
    healthy.assert_not_called()


def test_start_llama_server_skips_when_already_healthy(monkeypatch):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", lambda: True)
    assert main.start_llama_server() is None


def test_start_llama_server_skips_missing_model(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("AI_CAR_DISABLE_LLM_AUTOSTART", raising=False)
    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    monkeypatch.setattr(main, "_resolve_model_path", lambda: tmp_path / "missing.gguf")
    assert main.start_llama_server() is None
    assert "model not found" in capsys.readouterr().err
