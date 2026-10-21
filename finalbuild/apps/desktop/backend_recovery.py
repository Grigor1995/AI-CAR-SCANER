"""Safely recover a Desktop-owned FastAPI child; never touch external backends.

Runs checks/restarts in a daemon thread (not Qt's event loop). Only services
launched or explicitly requested by Desktop are eligible for recovery.
"""
from __future__ import annotations

from collections import deque
import logging
import threading
import time
from typing import Callable, Protocol

logger = logging.getLogger(__name__)


class BackendProcess(Protocol):
    def poll(self) -> int | None: ...


class BackendRecoverySupervisor:
    def __init__(
        self,
        *,
        process: Callable[[], BackendProcess | None],
        restart: Callable[[], object],
        healthy: Callable[[], bool],
        poll_seconds: float = 3.0,
        max_restarts: int = 3,
        window_seconds: float = 120.0,
        allow_initial_retry: bool = False,
    ) -> None:
        if poll_seconds <= 0 or max_restarts < 1 or window_seconds <= 0:
            raise ValueError("Invalid backend recovery configuration")
        self.process = process
        self.restart = restart
        self.healthy = healthy
        self.poll_seconds = poll_seconds
        self.max_restarts = max_restarts
        self.window_seconds = window_seconds
        self.allow_initial_retry = allow_initial_retry
        self.stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._attempts: deque[float] = deque()
        self._owned: BackendProcess | None = None
        self._next_retry_at = 0.0
        self.exhausted = False
        self.ever_healthy = False

    def start(self) -> bool:
        if self._thread is not None:
            return True
        self._owned = self.process()
        if self._owned is None and not self.allow_initial_retry:
            logger.info("FastAPI recovery skipped: backend not owned by this launcher")
            return False
        # When a healthy unrelated API is present, never take it over.
        if self._owned is None and self.healthy():
            logger.info("FastAPI recovery skipped: external API already healthy")
            return False
        self._thread = threading.Thread(
            target=self._loop, name="AI-Car-FastAPI-recovery", daemon=True
        )
        self._thread.start()
        return True

    def stop(self, *, join_timeout: float = 8.0) -> None:
        self.stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=join_timeout)
            if thread.is_alive():
                logger.error("FastAPI recovery thread still active at shutdown")

    def _loop(self) -> None:
        while not self.stop_event.wait(self.poll_seconds):
            self.check_once()

    def check_once(self) -> str:
        """Run a single poll; deterministic tests can call this without threads."""
        if self.stop_event.is_set() or self.exhausted:
            return "stopped"
        owned = self.process()
        if owned is not None:
            self._owned = owned
            if owned.poll() is None:
                return "running"
        elif self._owned is None and not self.allow_initial_retry:
            return "external"

        # A healthy service on the same port may have started independently.
        if self.healthy():
            self.ever_healthy = True
            return "external"
        now = time.monotonic()
        if now < self._next_retry_at:
            return "backoff"
        while self._attempts and (now - self._attempts[0]) >= self.window_seconds:
            self._attempts.popleft()
        if len(self._attempts) >= self.max_restarts:
            self.exhausted = True
            logger.error(
                "FastAPI restart budget exhausted: %d attempts in %.0fs",
                self.max_restarts, self.window_seconds,
            )
            return "exhausted"
        if self.stop_event.is_set():
            return "stopped"
        self._attempts.append(now)
        self._next_retry_at = now + min(
            self.poll_seconds * 2 ** (len(self._attempts) - 1), 30.0
        )
        logger.warning(
            "FastAPI local process exited; recovery %d/%d",
            len(self._attempts), self.max_restarts,
        )
        try:
            recovered = self.restart()
        except Exception:
            logger.exception("FastAPI recovery attempt failed")
            return "failed"
        if self.stop_event.is_set():
            return "stopped"
        candidate = self.process()
        if candidate is not None:
            self._owned = candidate
        elif recovered is not None and hasattr(recovered, "poll"):
            self._owned = recovered
        is_healthy = self.healthy()
        self.ever_healthy = self.ever_healthy or is_healthy
        return "recovered" if is_healthy else "failed"
