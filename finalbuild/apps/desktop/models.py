from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any

@dataclass
class Vehicle:
    make: str
    model: str
    chassis: str = ""
    year: int | None = None
    engine: str = ""
    fuel: list[str] = field(default_factory=list)
    ecu: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Vehicle":
        return cls(
            make=str(data.get("make", "Unknown")),
            model=str(data.get("model", "Vehicle")),
            year=int(data["year"]) if data.get("year") not in (None, "") else None,
            engine=str(data.get("engine", "")),
            fuel=[str(x) for x in data.get("fuel", [])],
            ecu=str(data.get("ecu", "")),
        )

@dataclass
class Session:
    session_id: str
    state: str = "CREATED"
    vehicle: Vehicle | None = None

@dataclass
class TestCandidate:
    test_id: str
    name: str
    purpose: str
    priority_score: float
    risk_level: str
    expected_information_gain: float = 0.0
    safety_notes: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "TestCandidate":
        return cls(
            test_id=str(data.get("test_id") or data.get("id") or ""),
            name=str(data.get("name", "Diagnostic test")),
            purpose=str(data.get("purpose", "")),
            priority_score=float(data.get("priority_score", 0.0)),
            risk_level=str(data.get("risk", data.get("risk_level", "LOW"))),
            expected_information_gain=float(data.get("expected_information_gain", 0.0)),
            safety_notes=[str(x) for x in data.get("safety_notes", [])],
        )
