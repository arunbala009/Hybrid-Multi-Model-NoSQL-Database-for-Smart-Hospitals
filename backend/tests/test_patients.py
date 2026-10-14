"""
Patient Management Route Tests
==============================
Verifies Patient CRUD, Pydantic validations, duplicate prevention (409),
safe deletion enforcement, and longitudinal clinical history querying.
"""

from fastapi.testclient import TestClient


def test_list_patients_pagination(client: TestClient):
    """Verifies pagination structure and default limit on /api/v1/patients."""
    res = client.get("/api/v1/patients?skip=0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data
    assert data["skip"] == 0
    assert data["limit"] == 10


def test_get_patient_success(client: TestClient):
    """Verifies fetching a single patient by ID."""
    res = client.get("/api/v1/patients/P1001")
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == "P1001"
    assert data["first_name"] == "Fictional"


def test_get_patient_not_found(client: TestClient):
    """Verifies 404 response for nonexistent patient."""
    res = client.get("/api/v1/patients/P_NONEXISTENT")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_create_patient_success(client: TestClient):
    """Verifies registering a new fictional patient."""
    payload = {
        "first_name": "Eleanor",
        "last_name": "Vane",
        "dob": "1991-03-22",
        "gender": "Female",
        "blood_group": "B+",
        "contact_phone": "+1-555-4422",
        "emergency_contact": "Charles Vane"
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["first_name"] == "Eleanor"
    assert data["blood_group"] == "B+"


def test_create_patient_duplicate_conflict(client: TestClient):
    """Verifies 409 Conflict when attempting to register an existing patient ID."""
    payload = {
        "patient_id": "EXISTING_P1001",
        "first_name": "Duplicate",
        "last_name": "Patient",
        "dob": "1980-01-01",
        "gender": "Male",
        "blood_group": "O+"
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"]


def test_create_patient_validation_error(client: TestClient):
    """Verifies Pydantic 422 Unprocessable Entity when required fields are missing."""
    res = client.post("/api/v1/patients", json={"first_name": "Incomplete"})
    assert res.status_code == 422


def test_safe_deletion_blocked_by_active_history(client: TestClient):
    """Verifies safe deletion blocks removing a patient who has active clinical encounters."""
    res = client.delete("/api/v1/patients/P_HAS_ENCOUNTERS")
    assert res.status_code == 409
    assert "safety protocol" in res.json()["detail"].lower()


def test_patient_history_retrieval(client: TestClient):
    """Verifies patient clinical history endpoint returns encounter details."""
    res = client.get("/api/v1/patients/P1001/history")
    assert res.status_code == 200
    data = res.json()
    assert "patient" in data
    assert "encounters" in data
