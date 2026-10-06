from __future__ import annotations
from vehicle.obd.protocols.elm327 import ELM327Protocol
from vehicle.obd.transport import DiagnosticTransport

class GenericObdClient:
    """Generic OBD-II client. No vendor-specific assumptions beyond ELM327-style AT commands."""
    def __init__(self, transport: DiagnosticTransport): self.transport=transport; self.protocol=ELM327Protocol()
    async def connect(self):
        await self.transport.connect()
        for cmd in self.protocol.INIT_COMMANDS: await self.command(cmd)
    async def disconnect(self): await self.transport.disconnect()
    async def command(self, cmd: str) -> str:
        await self.transport.write((cmd.strip()+"\r").encode("ascii"))
        return self.protocol.normalize(await self.transport.read_until())
    async def read_vin(self) -> str | None:
        raw=await self.command("0902");
        try:
            p=self.protocol.parse_hex_payload("0902", raw).payload
            text=bytes(x for x in p if 32 <= x <= 126).decode("ascii",errors="ignore")
            # Remove service bytes / framing while retaining VIN-like sequence.
            import re
            m=re.search(r"([A-HJ-NPR-Z0-9]{17})",text)
            return m.group(1) if m else None
        except Exception: return None
    async def read_dtcs(self):
        raw=await self.command("03"); return self.protocol.dtc_codes(self.protocol.parse_hex_payload("03",raw).payload)
    async def read_pid(self,pid:int):
        data=self.protocol.parse_pid(pid, await self.command(f"010{pid:X}" if pid < 0x10 else f"01{pid:02X}"))
        return data
    async def read_standard_live_data(self):
        values={}
        for pid,name,decoder in [(0x0C,"rpm",self.protocol.rpm),(0x05,"coolant_c",self.protocol.coolant_c),(0x0D,"speed_kmh",self.protocol.speed_kmh),(0x11,"throttle_percent",self.protocol.throttle_percent)]:
            try: values[name]=decoder(await self.read_pid(pid))
            except Exception: values[name]=None
        return values
