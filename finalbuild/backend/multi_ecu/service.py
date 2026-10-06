from __future__ import annotations
from uuid import UUID
from vehicle.network.models import EcuNode, GatewayNode, VehicleNetworkTopology
from vehicle.network.runtime import MultiEcuRuntime
from .models import MultiEcuConnectRequest

class MultiEcuDiagnosticService:
    def __init__(self):
        self.runtimes: dict[UUID, MultiEcuRuntime] = {}

    async def connect(self, session_id: UUID, request: MultiEcuConnectRequest):
        existing = self.runtimes.get(session_id)
        if existing and existing.connected:
            return existing
        nodes = []
        for ecu in request.ecus:
            nodes.append(EcuNode(
                ecu_id=ecu.ecu_id, name=ecu.name, request_id=ecu.request_id,
                response_id=ecu.response_id, bus=ecu.bus, gateway_id=ecu.gateway_id,
                address_type=ecu.address_type, capabilities=frozenset(ecu.capabilities),
                metadata={
                    'vin': ecu.vin or 'VINTEST1234567890',
                    'software_version': ecu.software_version or f'{ecu.ecu_id}-SW-1.0',
                    'hardware_version': ecu.hardware_version or f'{ecu.ecu_id}-HW-1.0',
                    'dtc_records': ecu.dtc_records or [(0x030200, 0x28)],
                },
            ))
        gateways = tuple(GatewayNode(gateway_id=g.gateway_id, name=g.name, bus=g.bus) for g in request.gateways)
        topology = VehicleNetworkTopology(ecus=tuple(nodes), gateways=gateways)
        runtime = MultiEcuRuntime(session_id=session_id, topology=topology)
        await runtime.connect()
        self.runtimes[session_id] = runtime
        return runtime

    async def disconnect(self, session_id: UUID):
        runtime = self.require(session_id)
        await runtime.disconnect()
        return runtime

    def require(self, session_id: UUID) -> MultiEcuRuntime:
        runtime = self.runtimes.get(session_id)
        if runtime is None:
            raise KeyError(session_id)
        return runtime
