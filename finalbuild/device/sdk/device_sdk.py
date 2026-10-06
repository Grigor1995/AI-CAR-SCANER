from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class DeviceCapabilities:
    obd: bool=False; can: bool=False; can_fd: bool=False; uds: bool=False; ble: bool=False; wifi: bool=False; usb: bool=False

class DiagnosticDeviceSdk(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def get_capabilities(self) -> DeviceCapabilities: ...
    async def health(self) -> dict: ...

class OfflinePolicy:
    """Documents which operations may continue when the backend is unavailable."""
    allowed_offline = {"create_session", "add_evidence", "save_measurement", "read_dtc", "read_live_data", "run_local_rule", "queue_sync"}
    def can_run(self, operation: str) -> bool:
        return operation in self.allowed_offline
