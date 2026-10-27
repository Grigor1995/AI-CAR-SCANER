from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any
import re


def fuel_values(value) -> list[str]:
    """Accept catalog strings and API lists, repairing old letter-split profiles."""
    if isinstance(value, str):
        values = re.split(r"[,+/]", value)
    elif isinstance(value, (list, tuple)):
        values = value
    else:
        return []
    values = [str(item).strip() for item in values if str(item).strip()]
    if len(values) > 1 and all(len(item) == 1 for item in values):
        word = "".join(values)
        if word.casefold() in {"diesel", "petrol", "gasoline", "lpg", "cng", "hybrid", "electric", "phev", "hev"}:
            return [word]
    return values

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
            chassis=str(data.get("chassis") or ""),
            year=int(data["year"]) if data.get("year") not in (None, "") else None,
            engine=str(data.get("engine") or ""),
            fuel=fuel_values(data.get("fuel", [])),
            ecu=str(data.get("ecu") or ""),
        )

@dataclass
class Session:
    session_id: str
    state: str = "CREATED"
    vehicle: Vehicle | None = None

@dataclass
class TestCandidate:
    __test__ = False  # Prevent pytest from treating this data model as a test class.

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


def user_report_data(value):
    """Create an export snapshot without internal session identifiers."""
    if isinstance(value, dict):
        return {key: user_report_data(item) for key, item in value.items() if key != "session_id"}
    if isinstance(value, list):
        return [user_report_data(item) for item in value]
    return value
