from diagnostic.models import DiagnosticSession
from device.manager import vci_manager
from diagnostic.session_persistence import persistence

# Fast in-process registry used by the diagnostic engines.
# The configured database is the durable/shared source of truth.
sessions: dict[str, DiagnosticSession] = {}


def load_persisted_sessions() -> None:
    sessions.update(persistence.load())


def persist_sessions() -> None:
    persistence.save_all(sessions)
