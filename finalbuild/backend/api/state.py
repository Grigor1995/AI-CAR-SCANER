from diagnostic.models import DiagnosticSession

# In-memory session registry for the current API process.
# VCI connection management is handled by the acquisition/device services;
# api.state must not import a legacy vehicle.devices module that no longer exists.
sessions: dict[str, DiagnosticSession] = {}
