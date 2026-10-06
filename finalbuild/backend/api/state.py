from diagnostic.models import DiagnosticSession
from vehicle.devices.connection import VCIConnectionManager

sessions: dict[str, DiagnosticSession] = {}
vci_manager = VCIConnectionManager()
