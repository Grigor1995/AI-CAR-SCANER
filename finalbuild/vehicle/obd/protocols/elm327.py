from __future__ import annotations
import re
from dataclasses import dataclass

class OBDProtocolError(ValueError):
    pass

@dataclass(frozen=True)
class OBDResponse:
    command: str
    raw: str
    payload: bytes

class ELM327Protocol:
    """Transport-agnostic ELM327 command builder/parser for generic OBD-II."""
    INIT_COMMANDS = ("ATZ", "ATE0", "ATL0", "ATS0", "ATSP0")

    @staticmethod
    def normalize(raw: str | bytes) -> str:
        if isinstance(raw, bytes):
            raw = raw.decode("ascii", errors="ignore")
        return raw.replace("\r", " ").replace("\n", " ").replace(">", " ").strip()

    @classmethod
    def parse_hex_payload(cls, command: str, raw: str | bytes) -> OBDResponse:
        text = cls.normalize(raw).upper()
        if any(x in text for x in ("NO DATA", "ERROR", "UNABLE TO CONNECT", "BUS INIT")):
            raise OBDProtocolError(text)
        tokens = re.findall(r"(?<![0-9A-F])[0-9A-F]{2}(?![0-9A-F])", text)
        if not tokens:
            raise OBDProtocolError(f"No hexadecimal payload in response: {text!r}")
        return OBDResponse(command=command.upper().replace(" ", ""), raw=text, payload=bytes.fromhex("".join(tokens)))

    @classmethod
    def parse_pid(cls, pid: int, raw: str | bytes) -> bytes:
        response = cls.parse_hex_payload(f"01{pid:02X}", raw)
        expected = bytes((0x40 + 0x01, pid))
        idx = response.payload.find(expected)
        if idx < 0:
            # Some adapters omit the service header; retain last bytes as fallback.
            if len(response.payload) >= 2:
                return response.payload[-2:]
            raise OBDProtocolError(f"PID 01{pid:02X} not present")
        return response.payload[idx + 2:]

    @staticmethod
    def rpm(data: bytes) -> float:
        if len(data) < 2: raise OBDProtocolError("RPM requires 2 data bytes")
        return ((data[0] << 8) | data[1]) / 4.0

    @staticmethod
    def coolant_c(data: bytes) -> float:
        if not data: raise OBDProtocolError("Coolant requires 1 data byte")
        return data[0] - 40.0

    @staticmethod
    def speed_kmh(data: bytes) -> float:
        if not data: raise OBDProtocolError("Speed requires 1 data byte")
        return float(data[0])

    @staticmethod
    def throttle_percent(data: bytes) -> float:
        if not data: raise OBDProtocolError("Throttle requires 1 data byte")
        return data[0] * 100.0 / 255.0

    @staticmethod
    def dtc_codes(payload: bytes) -> list[str]:
        # Mode 03 payload is pairs of bytes; first service/header bytes are skipped if present.
        if len(payload) >= 2 and payload[0] == 0x43:
            payload = payload[1:]
        result=[]
        for i in range(0, len(payload)-1, 2):
            a,b=payload[i],payload[i+1]
            if a == 0 and b == 0: continue
            chars="PCBU"
            code=chars[(a >> 6) & 0x03] + f"{a & 0x3F:02X}{b:02X}"
            result.append(code)
        return result
