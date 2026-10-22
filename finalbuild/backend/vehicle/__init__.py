"""Compatibility import shim to one canonical vehicle-core implementation.

The authoritative shared Python vehicle core is finalbuild/vehicle/ and is
used by FastAPI. This prevents backend/vehicle stub modules from shadowing real
ELM327/UDS/J2534 modules when PYTHONPATH order changes at startup.
"""
from pathlib import Path

_SHARED_CORE = Path(__file__).resolve().parents[2] / "vehicle"
if not _SHARED_CORE.is_dir():
    raise ImportError("Shared vehicle core was not bundled: " + str(_SHARED_CORE))
__path__ = [str(_SHARED_CORE)]
from .interfaces import *  # noqa: F401,F403
