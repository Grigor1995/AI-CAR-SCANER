from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class DeviceMode(str, Enum):
    NORMAL = "normal"
    DIAGNOSTIC = "diagnostic"
    RECOVERY = "recovery"
    OTA = "ota"

@dataclass
class AndroidDeviceInfo:
    device_id: str
    model: str
    serial: str | None = None
    app_version: str = "0.1.0"
    firmware_version: str = "0.1.0"
    mode: DeviceMode = DeviceMode.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)

class DeviceStateMachine:
    allowed = {
        DeviceMode.NORMAL: {DeviceMode.DIAGNOSTIC, DeviceMode.OTA, DeviceMode.RECOVERY},
        DeviceMode.DIAGNOSTIC: {DeviceMode.NORMAL, DeviceMode.OTA, DeviceMode.RECOVERY},
        DeviceMode.OTA: {DeviceMode.NORMAL, DeviceMode.RECOVERY},
        DeviceMode.RECOVERY: {DeviceMode.NORMAL, DeviceMode.OTA},
    }
    def __init__(self, initial: DeviceMode = DeviceMode.NORMAL):
        self.mode = initial
    def transition(self, target: DeviceMode) -> DeviceMode:
        if target not in self.allowed[self.mode]:
            raise ValueError(f"Invalid device transition: {self.mode} -> {target}")
        self.mode = target
        return self.mode
