"""Bounded recovery supervisor for a Desktop-owned local FastAPI process.

Never manages remote/Render backends, never takes over an unrelated process,
and never restarts intentionally stopped services. All potentially blocking
operations happen outside the Qt UI thread.
"""
from __future__ import annotations

from collections import deque
import logging
import threading
import time
from typing import Callable, Protocol


log = logging.getLogger(__name__)


class ChildProcess(Protocol):
    def poll(self) -> int | None: ...


class BackendRecoverySupervisor:
    def __init__(
        self,
        *,
        process: Callable[[], ChildProcess | None],
        restart: Callable[[], object],
        healthy: Callable[[], bool],
        poll_seconds: float = 3.0,
        max_restarts: int = 3,
        window_seconds: float = 120.0,
        allow_initial_retry: bool = False,
    ) -> None:
        if poll_seconds <= 0 or max_restarts < 1 or window_seconds <= 0:
            raise ValueError("Invalid recovery configuration")
        self.process = process
        self.restart = restart
        self.healthy = healthy
        self.poll_seconds = poll_seconds
        self.max_restarts = max_restarts
        self.window_seconds = window_seconds
        self.allow_initial_retry = allow_initial_retry
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._attempts: deque[float] = deque()
        self._last_owned: ChildProcess | None = None
        self._next_allowed = 0.0
        self.exhausted = False

    def start(self) -> None:
        if self._thread is not None:
            return
        # Only a process created by THIS launcher is eligible for recovery.
        self._last_owned = self.process()
        if self._last_owned is None and (
            not self.allow_initial_retry or self.healthy()
        ):
            log.info("FastAPI auto-recovery disabled: backend is external or absent")
            return
        self._thread = threading.Thread(
            target=self._loop, name="FastAPI-recovery", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and threading.current_thread() is not thread:
            thread.join(timeout=20.0)

    def _loop(self) -> None:
        while not self._stop.wait(self.poll_seconds):
            self.check_once()

    def check_once(self) -> str:
        """One deterministic iteration, also callable by unit tests."""
        if self._stop.is_set() or self.exhausted:
            return "stopped"
        owned = self.process()
        if owned is not None:
            self._last_owned = owned
        elif self._last_owned is None and not self.allow_initial_retry:
            return "external"
        if owned is not None and owned.poll() is None:
            return "running"
        # Don't spawn a competing API if another healthy service took the port.
        if self.healthy():
            return "external"
        now = time.monotonic()
        if now < self._next_allowed:
            return "backoff"
        while self._attempts and now - self._attempts[0] >= self.window_seconds:
            self._attempts.popleft()
        if len(self._attempts) >= self.max_restarts:
            self.exhausted = True
            log.error("FastAPI auto-recovery exhausted (%d attempts / %.0fs)", self.max_restarts, self.window_seconds)
            return "exhausted"
        self._attempts.append(now)
        self._next_allowed = now + min(self.poll_seconds * (2 ** (len(self._attempts) - 1)), 30.0)
        if self._stop.is_set():
            return "stopped"
        log.warning("FastAPI exited unexpectedly; attempting local restart %d/%d", len(self._attempts), self.max_restarts)
        try:
            recovered = self.restart()
        except Exception:
            log.exception("FastAPI auto-restart failed")
            return "failed"
        self._last_owned = self.process() or recovered or self._last_owned
        return "recovered" if self.healthy() else "failed"
