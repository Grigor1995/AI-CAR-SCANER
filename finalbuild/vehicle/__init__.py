"""Compatibility import path. All vehicle implementation is under backend/vehicle."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parents[1] / 'backend' / 'vehicle')]
from .interfaces import *  # noqa: F401,F403
