from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DeviceConnectionError(RuntimeError):
    pass


class DeviceStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"


@dataclass
class DeviceCapabilities:
    obd: bool = True
    can: bool = True
    uds: bool = True


@dataclass
class DeviceDescriptor:
    device_id: str
    manufacturer: str = "AI-CAR-SCANER"
    model: str = "Simulator"
    firmware_version: str | None = None
    protocol: str = "OBD/CAN"
    connection_type: str = "simulator"
    capabilities: DeviceCapabilities = field(default_factory=DeviceCapabilities)
    status: DeviceStatus = DeviceStatus.DISCONNECTED
    metadata: dict = field(default_factory=dict)


class VCIConnectionManager:
    """Deterministic simulator VCI manager until physical adapters are injected."""

    def __init__(self):
        self.devices: dict[str, DeviceDescriptor] = {}
        self.connections: dict[str, dict] = {}

    def add_simulator(self) -> DeviceDescriptor:
        device = DeviceDescriptor(
            device_id="simulator-vci",
            status=DeviceStatus.DISCONNECTED,
        )
        self.devices[device.device_id] = device
        self.connections.pop(device.device_id, None)
        return device

    async def scan(self, transport: str, timeout: float = 3.0):
        if transport.lower() != "simulator":
            raise DeviceConnectionError("Only simulator transport is available in this phase")
        return [self.add_simulator()]

    async def probe_wifi(self, host: str, port: int, timeout: float):
        raise DeviceConnectionError("Wi-Fi physical probing is not available in this phase")

    async def connect(self, device_id: str, config: dict | None = None):
        device = self._get(device_id)
        device.status = DeviceStatus.CONNECTED
        self.connections[device_id] = dict(config or {})
        return device

    async def reconnect(self, device_id: str):
        return await self.connect(device_id, self.connections.get(device_id, {}))

    async def disconnect(self, device_id: str):
        device = self._get(device_id)
        device.status = DeviceStatus.DISCONNECTED
        return device

    def status(self, device_id: str) -> DeviceDescriptor:
        return self._get(device_id)

    async def read_vin(self, device_id: str):
        self._require_connected(device_id)
        return "WDD2110801A123456"

    async def read_dtcs(self, device_id: str):
        self._require_connected(device_id)
        return ["P0102"]

    async def read_live_data(self, device_id: str):
        self._require_connected(device_id)
        return {
            "rpm": 1696.0,
            "coolant_temp_c": 50.0,
            "vehicle_speed_kmh": 40.0,
            "throttle_pct": 52.0,
        }

    def _get(self, device_id: str) -> DeviceDescriptor:
        device = self.devices.get(device_id)
        if device is None:
            raise DeviceConnectionError(f"Device not found: {device_id}")
        return device

    def _require_connected(self, device_id: str) -> DeviceDescriptor:
        device = self._get(device_id)
        if device.status != DeviceStatus.CONNECTED:
            raise DeviceConnectionError(f"Device is not connected: {device_id}")
        return device


vci_manager = VCIConnectionManager()
