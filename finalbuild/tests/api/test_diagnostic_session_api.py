from fastapi.testclient import TestClient

from api.main import app


def test_create_add_symptom_dtc_and_analyze():
    client = TestClient(app)

    vehicle = {
        "make": "Mercedes-Benz",
        "model": "W211 E350",
        "year": 2006,
        "engine": "M272 3.5",
        "fuel": ["petrol", "LPG"],
        "ecu": "ME 9.7",
    }
    response = client.post("/api/v1/sessions", json=vehicle)
    assert response.status_code == 200, response.text
    session_id = response.json()["session_id"]

    symptom = (
        "Engine runs smoothly on petrol, but shakes and hesitates on LPG "
        "when accelerating below 2000 RPM. The problem is more noticeable "
        "when accelerating from low RPM under load. At idle, the engine is "
        "mostly smooth. Switching back to petrol significantly reduces the symptom."
    )
    response = client.post(
        f"/api/v1/sessions/{session_id}/symptoms",
        json={"raw_text": symptom, "symptom": symptom},
    )
    assert response.status_code == 200, response.text
    assert response.json()["symptoms"][0]["raw_text"] == symptom
    symptom_id = response.json()["symptoms"][0]["id"]

    updated = "Engine shakes on LPG below 2000 RPM under load."
    response = client.put(
        f"/api/v1/sessions/{session_id}/symptoms/{symptom_id}",
        json={"raw_text": updated, "symptom": updated},
    )
    assert response.status_code == 200, response.text
    assert response.json()["symptoms"][0]["id"] == symptom_id
    assert response.json()["symptoms"][0]["raw_text"] == updated

    response = client.delete(
        f"/api/v1/sessions/{session_id}/symptoms/{symptom_id}"
    )
    assert response.status_code == 200, response.text
    assert response.json()["symptoms"] == []

    response = client.post(
        f"/api/v1/sessions/{session_id}/dtcs",
        json={"code": "P0302"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["dtcs"][0]["code"] == "P0302"

    response = client.post(f"/api/v1/analysis/{session_id}")
    assert response.status_code == 200, response.text

    body = response.json()
    categories = {item["category"] for item in body["hypotheses"]}
    assert "ignition / combustion" in categories
    assert "LPG fuel delivery / mixture" in categories
    assert "air-fuel / intake" in categories
    assert "mechanical cylinder condition" in categories
    assert all("confirmed coil failure" not in item["statement"].lower() for item in body["hypotheses"])


def test_legacy_symptom_payload_is_accepted():
    client = TestClient(app)
    response = client.post("/api/v1/sessions", json={})
    assert response.status_code == 200, response.text
    session_id = response.json()["session_id"]

    response = client.post(
        f"/api/v1/sessions/{session_id}/symptoms",
        json={"symptom": "Engine shakes on LPG"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["symptoms"][0]["raw_text"] == "Engine shakes on LPG"
