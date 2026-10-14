"""
Doctor Management Route Tests
=============================
Verifies Doctor directory queries, specialty filtering, and safe deletion.
"""

from fastapi.testclient import TestClient


def test_list_doctors_with_specialty_filter(client: TestClient):
    """Verifies filtering physicians by clinical specialty."""
    res = client.get("/api/v1/doctors?specialty=Cardiology")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_get_doctor_details(client: TestClient):
    """Verifies fetching physician profile."""
    res = client.get("/api/v1/doctors/DOC101")
    assert res.status_code == 200
    data = res.json()
    assert data["doctor_id"] == "DOC101"
    assert data["specialty"] == "Cardiology"


def test_create_doctor_success(client: TestClient):
    """Verifies creating a new physician record."""
    payload = {
        "first_name": "Gregory",
        "last_name": "House",
        "specialty": "Infectious Disease",
        "license_number": "MD-INF-4040",
        "department_id": "DEP04",
        "years_of_experience": 20
    }
    res = client.post("/api/v1/doctors", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["specialty"] == "Infectious Disease"


def test_doctor_deletion_blocked_by_active_cases(client: TestClient):
    """Verifies physician cannot be deleted if assigned to active clinical cases."""
    res = client.delete("/api/v1/doctors/DOC_HAS_CASES")
    assert res.status_code == 409
    assert "assigned to" in res.json()["detail"].lower()
