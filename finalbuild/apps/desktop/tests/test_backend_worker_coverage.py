"""Real backend-worker entrypoint behavior, without opening any server ports."""
from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from apps.desktop import backend_worker


@pytest.mark.parametrize(
    ("frozen", "configured_port", "configured_host", "configured_log"),
    [
        (False, None, None, None),
        (False, "8123", "0.0.0.0", "debug"),
        (True, "8302", "127.0.0.1", "warning"),
    ],
)
def test_backend_worker_routes_to_uvicorn_with_explicit_config(
    monkeypatch, tmp_path, frozen, configured_port, configured_host, configured_log
):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    monkeypatch.setattr(backend_worker.sys, "frozen", frozen, raising=False)
    monkeypatch.setattr(backend_worker.sys, "_MEIPASS", str(bundle), raising=False)

    for var, value in (
        ("AI_CAR_BACKEND_PORT", configured_port),
        ("AI_CAR_BACKEND_HOST", configured_host),
        ("AI_CAR_BACKEND_LOG_LEVEL", configured_log),
    ):
        if value is None:
            monkeypatch.delenv(var, raising=False)
        else:
            monkeypatch.setenv(var, value)

    launch = Mock()
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=launch))
    original_path = list(sys.path)
    try:
        backend_worker.main()
        expected_backend = (
            bundle / "backend" if frozen else Path(backend_worker.__file__).resolve().parents[2] / "backend"
        )
        assert str(expected_backend) in sys.path
        launch.assert_called_once_with(
            "api.main:app",
            host=configured_host or "127.0.0.1",
            port=int(configured_port or "8001"),
            log_level=configured_log or "info",
            workers=1,
        )
        # A repeated call must not add duplicate sys.path entries.
        backend_worker.main()
        assert sys.path.count(str(expected_backend)) == 1
    finally:
        sys.path[:] = original_path


def test_backend_worker_fails_explicitly_for_invalid_backend_port(monkeypatch):
    monkeypatch.setenv("AI_CAR_BACKEND_PORT", "not-an-integer")
    mock_run = Mock()
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=mock_run))
    with pytest.raises(ValueError, match="invalid literal"):
        backend_worker.main()
    mock_run.assert_not_called()


@pytest.mark.parametrize("seed_error", [None, RuntimeError("catalog seed failed")])
def test_local_database_preparation_precedes_server_and_failures_block_startup(monkeypatch, seed_error):
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setenv("AI_CAR_DESKTOP_LOCAL_DB", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test-local.db")
    monkeypatch.setenv("AI_CAR_BACKEND_PORT", "8001")
    events = []

    def prepare(url, root):
        assert url == "sqlite:///test-local.db"
        assert root == Path(backend_worker.__file__).resolve().parents[2]
        events.append("seed")
        if seed_error is not None:
            raise seed_error
        return 3

    launch = Mock(side_effect=lambda *args, **kwargs: events.append("serve"))
    monkeypatch.setitem(sys.modules, "diagnostic.local_database", SimpleNamespace(prepare_local_database=prepare))
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=launch))
    if seed_error is not None:
        with pytest.raises(RuntimeError, match="catalog seed failed"):
            backend_worker.main()
        launch.assert_not_called()
        assert events == ["seed"]
    else:
        backend_worker.main()
        launch.assert_called_once()
        assert events == ["seed", "serve"]
