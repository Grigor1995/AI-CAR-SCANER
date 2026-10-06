from dataclasses import dataclass

@dataclass
class ServiceStatus:
    name: str
    running: bool
    version: str

class DeviceServiceManager:
    def __init__(self): self._services = {}
    def register(self, status: ServiceStatus): self._services[status.name] = status
    def list(self): return list(self._services.values())
    def stop(self, name: str):
        if name in self._services:
            self._services[name].running = False
