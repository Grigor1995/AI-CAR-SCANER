"""Compatibility export; canonical report rendering belongs to the backend."""
import sys
from backend import reporting as _reporting
sys.modules[__name__] = _reporting
