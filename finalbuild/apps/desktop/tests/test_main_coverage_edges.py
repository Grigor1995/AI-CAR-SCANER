from __future__ import annotations

import io
import os
from pathlib import Path
from urllib.error import URLError
from unittest.mock import Mock

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


def test_start_llama_server_respects_disable_health_missing_model_and_busy_port(monkeypatch, capsys):
    monkeypatch.setenv("AI_CAR_DISABLE_LLM_AUTOSTART", "yes")
    assert main.start_llama_server() is None

    monkeypatch.setenv("AI_CAR_DISABLE_LLM_AUTOSTART", "0")
    monkeypatch.setattr(main, "_llm_healthy", lambda: True)
    assert main.start_llama_server() is None

    monkeypatch.setattr(main, "_llm_healthy", lambda: False)
    monkeypatch.setattr(main, "_resolve_model_path", lambda: Path("/missing/model.gguf"))
    assert main.start_llama_server() is None
    assert "model not found" in capsys.readouterr().err

    model = Path("/fake/model.gguf")
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
