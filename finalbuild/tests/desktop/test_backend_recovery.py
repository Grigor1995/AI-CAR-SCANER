"""FastAPI local recovery never touches cloud or external healthy instances."""
from __future__ import annotations

from types import SimpleNamespace

from apps.desktop.backend_recovery import BackendRecoverySupervisor


def test_no_recovery_for_external_service():
    calls = []
    monitor = BackendRecoverySupervisor(
        process=lambda: None,
        restart=lambda: calls.append("restart"),
        healthy=lambda: True,
    )
    monitor.start()
    assert monitor.check_once() == "external"
    monitor.stop()
    assert calls == []


def test_restart_crashed_owned_process(monkeypatch):
    import apps.desktop.backend_recovery as recovery
    clock = [100.0]
    monkeypatch.setattr(recovery.time, "monotonic", lambda: clock[0])
    current = [SimpleNamespace(poll=lambda: 12)]
    calls = []

    def restart():
        calls.append("restart")
        current[0] = SimpleNamespace(poll=lambda: None)
        return current[0]

    monitor = BackendRecoverySupervisor(
        process=lambda: current[0],
        restart=restart,
        healthy=lambda: bool(calls),
        poll_seconds=1,
    )
    assert monitor.check_once() == "recovered"
    assert calls == ["restart"]
    assert monitor.check_once() == "running"


def test_crashes_are_bounded_with_backoff(monkeypatch):
    import apps.desktop.backend_recovery as recovery
    now = [100.0]
    monkeypatch.setattr(recovery.time, "monotonic", lambda: now[0])
    dead = SimpleNamespace(poll=lambda: 1)
    count = []

    def failing_restart():
        count.append(1)
        raise OSError("backend unavailable")

    monitor = BackendRecoverySupervisor(
        process=lambda: dead, restart=failing_restart,
        healthy=lambda: False, poll_seconds=1.0, max_restarts=2,
    )
    assert monitor.check_once() == "failed"
    assert monitor.check_once() == "backoff"
    now[0] += 2
    assert monitor.check_once() == "failed"
    now[0] += 4
    assert monitor.check_once() == "exhausted"
    assert monitor.check_once() == "stopped"
    assert len(count) == 2


def test_shutdown_disables_recovery():
    calls = []
    dead = SimpleNamespace(poll=lambda: 1)
    monitor = BackendRecoverySupervisor(
        process=lambda: dead,
        restart=lambda: calls.append(1),
        healthy=lambda: False,
    )
    monitor.stop()
    assert monitor.check_once() == "stopped"
    assert not calls


def test_healthy_external_backend_prevents_duplicate_start():
    calls = []
    dead = SimpleNamespace(poll=lambda: 1)
    monitor = BackendRecoverySupervisor(
        process=lambda: dead,
        restart=lambda: calls.append(1),
        healthy=lambda: True,
    )
    assert monitor.check_once() == "external"
    assert calls == []
