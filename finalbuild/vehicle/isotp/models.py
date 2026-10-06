from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class IsoTpError(Exception): pass
class IsoTpTimeout(IsoTpError): pass
class IsoTpProtocolError(IsoTpError): pass

class FlowStatus(int, Enum):
    CTS = 0
    WAIT = 1
    OVERFLOW = 2

@dataclass(frozen=True)
class FlowControl:
    status: FlowStatus
    block_size: int = 0
    st_min: int = 0
