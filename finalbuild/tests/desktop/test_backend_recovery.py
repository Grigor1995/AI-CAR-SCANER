"""Deterministic tests for Desktop-owned FastAPI recovery, no network/CI."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.desktop.backend_recovery import BackendRecoverySupervisor


def process(exit_code=None):
    return SimpleNamespace(poll=lambda: exit_code)


def test_recovery_never_claims_healthy_external_api():
    calls = []
    supervisor = BackendRecoverySupervisor(
        process=lambda: None, restart=lambda: calls.append("spawn"), healthy=lambda: True,
        allow_initial_retry=True,
    )
    assert supervisor.start() is False
    assert supervisor.check_once() == "external"
    assert calls == []


def test_initial_failure_retries_then_restores_owned_process(monkeypatch):
    import apps.desktop.backend_recovery as module
    monkeypatch.setattr(module.time, "monotonic", lambda: 100)
    owned = [None]
    attempts = []
    def restart():
        attempts.append(1)
        owned[0] = process()
        return owned[0]
    sup = BackendRecoverySupervisor(
        process=lambda: owned[0], restart=restart,
        healthy=lambda: bool(attempts), allow_initial_retry=True,
    )
    assert sup.check_once() == "recovered"
    assert sup.check_once() == "running"
    assert attempts == [1]


def test_crash_recovery_is_bounded_with_backoff(monkeypatch):
    import apps.desktop.backend_recovery as module
    clock = [100]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    calls = []
    def fail():
        calls.append(1)
        raise RuntimeError("backend crash")
    sup = BackendRecoverySupervisor(
        process=lambda: process(7), restart=fail, healthy=lambda: False,
        poll_seconds=1, max_restarts=2, window_seconds=120,
    )
    assert sup.check_once() == "failed"
    assert sup.check_once() == "backoff"
    clock[0] += 2
    assert sup.check_once() == "failed"
    clock[0] += 4
    assert sup.check_once() == "exhausted"
    assert sup.check_once() == "stopped"
    assert len(calls) == 2


def test_attempt_window_expires(monkeypatch):
    import apps.desktop.backend_recovery as module
    clock = [100]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    calls = []
    sup = BackendRecoverySupervisor(
        process=lambda: process(1), restart=lambda: calls.append(1),
        healthy=lambda: False, poll_seconds=1,
        max_restarts=1, window_seconds=10,
    )
    assert sup.check_once() == "failed"
    clock[0] += 12
    assert sup.check_once() == "failed"
    assert calls == [1, 1]


def test_stop_disables_restart():
    calls = []
    sup = BackendRecoverySupervisor(
        process=lambda: process(1), restart=lambda: calls.append(1),
        healthy=lambda: False,
    )
    sup.stop()
    assert sup.check_once() == "stopped"
    assert calls == []


def test_running_owned_child_is_left_alone():
    calls = []
    sup = BackendRecoverySupervisor(
        process=lambda: process(), restart=lambda: calls.append(1),
        healthy=lambda: False,
    )
    assert sup.check_once() == "running"
    assert calls == []


def test_healthy_backend_after_crash_is_not_taken_over():
    calls = []
    sup = BackendRecoverySupervisor(
        process=lambda: process(0), restart=lambda: calls.append(1),
        healthy=lambda: True,
    )
    assert sup.check_once() == "external"
    assert calls == []


@pytest.mark.parametrize("kwargs", [
    {"poll_seconds": 0}, {"max_restarts": 0}, {"window_seconds": -2},
])
def test_invalid_configuration_rejected(kwargs):
    with pytest.raises(ValueError):
        BackendRecoverySupervisor(
            process=lambda: None, restart=lambda: None,
            healthy=lambda: False, **kwargs,
        )


def test_no_owned_process_no_initial_retry_means_no_thread():
    sup = BackendRecoverySupervisor(
        process=lambda: None, restart=lambda: None,
        healthy=lambda: False,
    )
    assert sup.start() is False
    assert sup._thread is None


def test_supervisor_thread_stops_on_user_shutdown():
    sup = BackendRecoverySupervisor(
        process=lambda: process(), restart=lambda: None,
        healthy=lambda: True, poll_seconds=0.01,
    )
    assert sup.start() is True
    sup.stop()
    assert sup._thread is not None
    assert not sup._thread.is_alive()
