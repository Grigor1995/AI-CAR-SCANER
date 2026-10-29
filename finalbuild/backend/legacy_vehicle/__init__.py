"""Historical simulator namespace; retained only for explicit compatibility imports.

Production vehicle imports resolve to backend/vehicle. No real adapter selects
these old simulator defaults implicitly.
"""
from .interfaces import *  # noqa: F401,F403
