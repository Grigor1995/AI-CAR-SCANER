"""Canonical vehicle stack, centralized with backend services.

Explicit backend.vehicle imports retain the historical simulator namespace.
Production top-level vehicle imports always use this canonical directory.
"""
from pathlib import Path
if __name__ == 'backend.vehicle':
    __path__ = [str(Path(__file__).resolve().parents[1] / 'legacy_vehicle')]
from .interfaces import *  # noqa: F401,F403
