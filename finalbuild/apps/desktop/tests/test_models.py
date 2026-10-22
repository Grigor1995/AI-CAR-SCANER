from apps.desktop.models import Session, TestCandidate, Vehicle


def test_vehicle_round_trip_preserves_all_fields():
    original = Vehicle("Mercedes-Benz", "E-Class", "W211", 2006, "M272", ["petrol", "lpg"], "ME9.7")
    decoded = Vehicle.from_json(original.to_json())

    assert decoded == original
    assert decoded.to_json()["fuel"] == ["petrol", "lpg"]


def test_vehicle_missing_fields_use_safe_defaults():
    vehicle = Vehicle.from_json({"make": None, "model": None, "year": "", "fuel": [1, None]})

    assert vehicle.make == "None"
    assert vehicle.model == "None"
    assert vehicle.chassis == ""
    assert vehicle.year is None
    assert vehicle.fuel == ["1", "None"]


def test_vehicle_accepts_numeric_year_string():
    assert Vehicle.from_json({"make": "Kia", "model": "Forte", "year": "2017"}).year == 2017


def test_vehicle_rejects_invalid_year():
    import pytest

    with pytest.raises(ValueError):
        Vehicle.from_json({"make": "Kia", "model": "Forte", "year": "unknown"})


def test_session_defaults_and_vehicle_reference():
    vehicle = Vehicle("Kia", "Forte")
    session = Session("session-1", vehicle=vehicle)

    assert session.session_id == "session-1"
    assert session.state == "CREATED"
    assert session.vehicle is vehicle


def test_test_candidate_accepts_aliases_and_converts_types():
    candidate = TestCandidate.from_json({
        "id": 123,
        "name": "Check LPG pressure",
        "priority_score": "0.75",
        "risk": "MEDIUM",
        "expected_information_gain": "0.9",
        "safety_notes": ["Ventilate workshop", 2],
    })

    assert candidate.test_id == "123"
    assert candidate.priority_score == 0.75
    assert candidate.risk_level == "MEDIUM"
    assert candidate.expected_information_gain == 0.9
    assert candidate.safety_notes == ["Ventilate workshop", "2"]


def test_test_candidate_defaults_when_optional_values_missing():
    candidate = TestCandidate.from_json({})

    assert candidate.test_id == ""
    assert candidate.name == "Diagnostic test"
    assert candidate.priority_score == 0.0
    assert candidate.risk_level == "LOW"
    assert candidate.safety_notes == []


def test_user_report_removes_nested_session_ids_without_mutating_internal_data():
    from apps.desktop.models import user_report_data
    original = {"session_id": "private", "dtcs": [{"code": "P0302"}],
                "details": [{"session_id": "nested", "result": "FAIL"}]}
    assert user_report_data(original) == {"dtcs": [{"code": "P0302"}], "details": [{"result": "FAIL"}]}
    assert original["session_id"] == "private"
    assert original["details"][0]["session_id"] == "nested"
