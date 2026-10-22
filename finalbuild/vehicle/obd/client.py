from __future__ import annotations
from vehicle.obd.protocols.elm327 import ELM327Protocol
from vehicle.obd.transport import DiagnosticTransport
import asyncio
from obd.protocols import initialization, detected_protocol

class GenericObdClient:
    """Generic OBD-II client. No vendor-specific assumptions beyond ELM327-style AT commands."""
    def __init__(self, transport: DiagnosticTransport, protocol_id: str = "auto"):
        self.transport=transport; self.protocol=ELM327Protocol(); self.protocol_id=protocol_id
        self._lock = asyncio.Lock()
    async def connect(self):
        commands = initialization(self.protocol_id)
        await self.transport.connect()
        try:
            for cmd in commands:
                reply = await self.command(cmd)
                if cmd.startswith("ATSP") and ("?" in reply or "ERROR" in reply.upper()):
                    raise ValueError("Adapter rejected selected OBD protocol")
            await self.command("0100")  # Let auto-search finish before short PID polls.
        except BaseException:
            await self.transport.disconnect()
            raise
    async def disconnect(self): await self.transport.disconnect()
    async def command(self, cmd: str) -> str:
        async with self._lock:
            try:
                await self.transport.write((cmd.strip()+"\r").encode("ascii"))
                raw = await self.transport.read_until(timeout=35 if cmd == "0100" else (10 if cmd == "0902" else 3))
                return raw.decode("ascii").rstrip("> \r\n")
            except BaseException:
                await self.transport.disconnect()
                raise
    async def protocol_status(self):
        await self.read_pid(0)  # Trigger auto negotiation before querying ATDPN.
        return detected_protocol(await self.command("ATDPN"))
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
    async def read_dtcs(self, mode: int = 3):
        if mode not in (3, 7, 10):
            raise ValueError("Only stored, pending and permanent DTC read services are supported")
        command = f"{mode:02X}"
        raw = await self.command(command)
        codes = []
        positive = False
        for payload in self.protocol.payloads(command, raw):
            if not payload.startswith(bytes([0x40+mode])):
                continue
            positive = True
            codes.extend(self.protocol.dtc_codes(payload))
        if not positive:
            raise ValueError("ECU did not return a positive DTC service response")
        return list(dict.fromkeys(codes))
    async def supported_pids(self):
        supported = set()
        for base in range(0, 0xE1, 0x20):
            data = await self.read_pid(base)
            if len(data) != 4:
                raise ValueError("Invalid supported PID bitmap")
            mask = int.from_bytes(data, "big")
            supported.update(base+i+1 for i in range(32) if mask & (1 << (31-i)))
            if not mask & 1:
                break
        return sorted(supported)
    async def read_pid(self,pid:int):
        data=self.protocol.parse_pid(pid, await self.command(f"010{pid:X}" if pid < 0x10 else f"01{pid:02X}"))
        return data
    async def read_standard_live_data(self):
        from obd.decoding import PIDS, decode_snapshot
        frames = {}
        for pid in PIDS:
            try:
                frames[pid.command] = await self.command(pid.command)
            except Exception:
                if not self.transport.connected:
                    raise
                frames[pid.command] = "NO DATA"
        return decode_snapshot(frames)["values"]
