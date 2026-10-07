from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from api.telemetry_routes import service as telemetry_service
from telemetry.models import TelemetrySample
from .models import AcquisitionStartRequest, AcquisitionStatus


@dataclass
class AcquisitionRecord:
    """Small API-facing record kept by the simulator acquisition service."""

    id: UUID = field(default_factory=uuid4)
    session_id: UUID | None = None
    timestamp_ms: int = 0
    channel: str = ""
    numeric_value: float | None = None
    unit: str | None = None
    sequence: int | None = None
    quality: str = "GOOD"
    metadata: dict = field(default_factory=dict)
    source_type: str = "OBD_ACQUISITION"
    raw: bytes | None = None


@dataclass
class _AcquisitionState:
    state: str = "STOPPED"
    records: list[AcquisitionRecord] = field(default_factory=list)
    task: asyncio.Task | None = None
    sequence: int = 0
    stats: dict[str, int] = field(default_factory=lambda: {
        "polls": 0,
        "records": 0,
        "errors": 0,
        "reconnects": 0,
    })


class AcquisitionApiService:
    """Simulator acquisition facade backed by the existing telemetry service."""

    def __init__(self):
        self._states: dict[UUID, _AcquisitionState] = {}

    async def start_simulator(
        self, session_id: UUID, request: AcquisitionStartRequest
    ) -> AcquisitionStatus:
        state = self._states.setdefault(session_id, _AcquisitionState())
        if state.task and not state.task.done():
            return self.status(session_id)

        state.state = "STARTING"
        state.stats = {"polls": 0, "records": 0, "errors": 0, "reconnects": 0}
        state.records.clear()
        state.sequence = 0
        state.task = asyncio.create_task(
            self._poll_simulator(session_id, state, request),
            name=f"acquisition-{session_id}",
        )
        state.state = "RUNNING"
        return self.status(session_id)

    async def _poll_simulator(
        self,
        session_id: UUID,
        state: _AcquisitionState,
        request: AcquisitionStartRequest,
    ) -> None:
        base_values = {
            0x0C: (750.0, "rpm"),
            0x05: (90.0, "C"),
            0x0D: (40.0, "km/h"),
            0x11: (32.0, "%"),
        }
        try:
            while True:
                now_ms = int(time.time() * 1000)
                samples: list[TelemetrySample] = []
                for pid in request.pids:
                    value, unit = base_values.get(pid, (0.0, None))
                    state.sequence += 1
                    state.records.append(AcquisitionRecord(
                        session_id=session_id,
                        timestamp_ms=now_ms,
                        channel=f"0x{pid:02X}",
                        numeric_value=value,
                        unit=unit,
                        sequence=state.sequence,
                        quality="GOOD",
                        metadata={"pid": pid, "adapter": "simulator"},
                    ))
                    samples.append(TelemetrySample(
                        session_id=session_id,
                        timestamp_ms=now_ms,
                        pid=f"0x{pid:02X}",
                        value=value,
                        unit=unit,
                        source="OBD_ACQUISITION",
                        sequence=state.sequence,
                    ))

                if samples:
                    telemetry_service.append(samples)
                state.stats["polls"] += 1
                state.stats["records"] += len(samples)
                await asyncio.sleep(request.poll_interval_ms / 1000.0)
        except asyncio.CancelledError:
            state.state = "STOPPED"
            raise
        except Exception:
            state.stats["errors"] += 1
            state.state = "ERROR"

    async def stop(self, session_id: UUID) -> AcquisitionStatus:
        state = self._require(session_id)
        if state.task and not state.task.done():
            state.task.cancel()
            try:
                await state.task
            except asyncio.CancelledError:
                pass
        state.task = None
        state.state = "STOPPED"
        return self.status(session_id)

    def status(self, session_id: UUID) -> AcquisitionStatus:
        state = self._require(session_id)
        return AcquisitionStatus(
            session_id=session_id,
            state=state.state,
            adapter="simulator",
            stats=state.stats.copy(),
            buffered_records=len(state.records),
            offline_queue_items=0,
        )

    def snapshot(self, session_id: UUID, limit: int = 100):
        return self._require(session_id).records[-limit:]

    def _require(self, session_id: UUID) -> _AcquisitionState:
        if session_id not in self._states:
            raise KeyError(session_id)
        return self._states[session_id]
