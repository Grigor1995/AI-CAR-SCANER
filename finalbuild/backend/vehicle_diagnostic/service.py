from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID

from vehicle.adapters.can_simulator import SimulatedCanBus
from vehicle.adapters.uds_simulator import UdsEcuSimulator
from vehicle.isotp.stack import IsoTpStack
from vehicle.protocol.trace import ProtocolTraceRecorder, TracedCanBus
from vehicle.uds.client import UdsClient
from vehicle.uds.diagnostics import UdsDiagnosticSession
from .models import DiagnosticRuntimeStatus


@dataclass
class _Runtime:
    adapter: str
    bus: object
    trace: ProtocolTraceRecorder
    uds: UdsDiagnosticSession
    connected: bool = True


class VehicleDiagnosticService:
    """Read-only ECU diagnostic runtime.

    Physical vendor transports are deliberately injected through the existing
    adapter seam. The HTTP server exposes only the deterministic simulator in
    Phase 16; desktop/mobile/device clients can construct the same protocol
    stack around a real CAN-capable adapter.
    """

    def __init__(self):
        self._runtimes: dict[UUID, _Runtime] = {}

    async def connect(self, session_id: UUID, *, adapter: str, request_id: int, response_id: int) -> DiagnosticRuntimeStatus:
        if adapter != 'simulator':
            raise NotImplementedError('Physical CAN/UDS adapters are device-side in Phase 16')
        existing = self._runtimes.get(session_id)
        if existing and existing.connected:
            return self.status(session_id)
        bus = SimulatedCanBus()
        recorder = ProtocolTraceRecorder(session_id=session_id)
        traced_bus = TracedCanBus(bus, recorder)
        UdsEcuSimulator(bus, request_id=request_id, response_id=response_id)
        isotp = IsoTpStack(traced_bus, request_id, response_id)
        client = UdsClient(isotp)
        runtime = _Runtime(adapter=adapter, bus=bus, trace=recorder, uds=UdsDiagnosticSession(client))
        self._runtimes[session_id] = runtime
        return self.status(session_id)

    async def disconnect(self, session_id: UUID) -> DiagnosticRuntimeStatus:
        runtime = self._require(session_id)
        runtime.connected = False
        return self.status(session_id)

    async def identify_ecu(self, session_id: UUID):
        runtime = self._require_connected(session_id)
        return await runtime.uds.identify_ecu()

    async def read_dtcs(self, session_id: UUID):
        runtime = self._require_connected(session_id)
        return await runtime.uds.read_dtcs()

    def trace(self, session_id: UUID, limit: int = 500):
        return self._require(session_id).trace.snapshot(limit)

    def status(self, session_id: UUID) -> DiagnosticRuntimeStatus:
        runtime = self._require(session_id)
        return DiagnosticRuntimeStatus(
            session_id=session_id,
            connected=runtime.connected,
            adapter=runtime.adapter,
            can=runtime.connected,
            isotp=runtime.connected,
            uds=runtime.connected,
            dtc_read=runtime.connected,
            dtc_clear=False,
            trace_events=len(runtime.trace.snapshot()),
        )

    def _require(self, session_id: UUID) -> _Runtime:
        runtime = self._runtimes.get(session_id)
        if runtime is None:
            raise KeyError(session_id)
        return runtime

    def _require_connected(self, session_id: UUID) -> _Runtime:
        runtime = self._require(session_id)
        if not runtime.connected:
            raise RuntimeError('diagnostic connection is stopped')
        return runtime
