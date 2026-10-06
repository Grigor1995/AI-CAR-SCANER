from __future__ import annotations
import tempfile
from pathlib import Path
from uuid import UUID
from vehicle.acquisition.manager import AcquisitionManager
from vehicle.acquisition.offline_queue import OfflineQueue
from vehicle.acquisition.models import ReconnectPolicy
from vehicle.acquisition.sources import ObdPollingSource
from vehicle.obd.client import GenericObdClient
from vehicle.obd.adapters.simulator import SimulatorTransport
from telemetry.models import TelemetrySample
from api.telemetry_routes import service as telemetry_service
from .models import AcquisitionStartRequest, AcquisitionStatus

class AcquisitionApiService:
    def __init__(self):
        self._managers: dict[UUID, AcquisitionManager] = {}
        self._queues: dict[UUID, OfflineQueue] = {}
        self._tempdir = Path(tempfile.gettempdir()) / 'ai-auto-diagnostic-acquisition'
        self._tempdir.mkdir(parents=True, exist_ok=True)

    async def start_simulator(self, session_id: UUID, request: AcquisitionStartRequest) -> AcquisitionStatus:
        existing = self._managers.get(session_id)
        if existing and existing.state.value != 'STOPPED': return self.status(session_id)
        responses = {
            '010C':'41 0C 0B B8','0105':'41 05 5A','010D':'41 0D 28','0111':'41 11 80',
            'ATZ':'ELM327 v2.2','ATE0':'OK','ATL0':'OK','ATS0':'OK','ATSP0':'OK'
        }
        client = GenericObdClient(SimulatorTransport(responses, dynamic=True))
        queue = OfflineQueue(self._tempdir / f'{session_id}.jsonl')
        async def telemetry_sink(records):
            samples = [TelemetrySample(session_id=session_id, timestamp_ms=r.timestamp_ms, pid=r.channel, value=r.numeric_value, unit=r.unit, source='OBD_ACQUISITION', sequence=r.sequence, quality='GOOD' if r.quality == 'GOOD' else 'INVALID', metadata=r.metadata) for r in records if r.numeric_value is not None]
            if samples:
                telemetry_service.append(samples)

        manager = AcquisitionManager(ObdPollingSource(client, request.pids), session_id=session_id, poll_interval_s=request.poll_interval_ms/1000.0, reconnect_policy=ReconnectPolicy(), offline_queue=queue, sink=telemetry_sink)
        await manager.start()
        self._managers[session_id]=manager; self._queues[session_id]=queue
        return self.status(session_id)

    async def stop(self, session_id: UUID) -> AcquisitionStatus:
        manager=self._require(session_id); await manager.stop(); return self.status(session_id)

    def status(self, session_id: UUID) -> AcquisitionStatus:
        manager=self._require(session_id)
        return AcquisitionStatus(session_id=session_id,state=manager.state.value,adapter='simulator',stats=manager.stats.copy(),buffered_records=len(manager.snapshot(1000000)),offline_queue_items=self._queues[session_id].size())

    def snapshot(self, session_id: UUID, limit: int = 100): return self._require(session_id).snapshot(limit)
    def _require(self, session_id: UUID) -> AcquisitionManager:
        if session_id not in self._managers: raise KeyError(session_id)
        return self._managers[session_id]
