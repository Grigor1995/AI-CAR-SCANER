from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, Field

class AcquisitionStartRequest(BaseModel):
    adapter: str = Field(default='simulator', pattern='^(simulator|ble|wifi|usb)$')
    poll_interval_ms: int = Field(default=100, ge=20, le=10_000)
    pids: list[int] = Field(default_factory=lambda: [0x0C,0x05,0x0D,0x11], max_length=32)

class AcquisitionStatus(BaseModel):
    session_id: UUID
    state: str
    adapter: str
    stats: dict[str, int]
    buffered_records: int
    offline_queue_items: int = 0
