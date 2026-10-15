"""
Patient Management Route Tests
==============================
Verifies Patient CRUD, Pydantic validations, duplicate prevention (409),
safe deletion enforcement, and longitudinal clinical history querying.
Tests all input validation boundaries: whitespace, short names, numeric names,
future dates of birth, phone numbers, emergency contacts, genders, and blood groups.
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
    """Verifies registering a new fictional patient with valid complete demographics."""
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
    assert data["emergency_contact"] == "Charles Vane"


def test_create_patient_name_trimming_success(client: TestClient):
    """Verifies whitespace around first and last names is trimmed upon registration."""
    payload = {
        "first_name": "  Eleanor  ",
        "last_name": "  Vane  ",
        "dob": "1991-03-22",
        "gender": "female",
        "blood_group": "b+",
        "contact_phone": " +1-555-4422 ",
        "emergency_contact": "  Charles Vane  "
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["first_name"] == "Eleanor"
    assert data["last_name"] == "Vane"
    assert data["gender"] == "Female"
    assert data["blood_group"] == "B+"
    assert data["contact_phone"] == "+1-555-4422"
    assert data["emergency_contact"] == "Charles Vane"


def test_create_patient_duplicate_conflict(client: TestClient):
    """Verifies 409 Conflict when attempting to register an existing patient ID."""
    payload = {
        "patient_id": "EXISTING_P1001",
        "first_name": "Duplicate",
        "last_name": "Patient",
        "dob": "1980-01-01",
        "gender": "Male",
        "blood_group": "O+",
        "emergency_contact": "Emergency Person"
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"]


def test_create_patient_validation_missing_fields(client: TestClient):
    """Verifies Pydantic 422 Unprocessable Entity when required fields are missing."""
    res = client.post("/api/v1/patients", json={"first_name": "Incomplete"})
    assert res.status_code == 422


def test_create_patient_whitespace_names_rejected(client: TestClient):
    """Rejects first or last names containing only whitespace."""
    base_payload = {
        "first_name": "   ",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "blood_group": "A+",
        "emergency_contact": "Jane Doe"
    }
    res = client.post("/api/v1/patients", json=base_payload)
    assert res.status_code == 422
    assert "at least 2 characters" in str(res.json()).lower()

    base_payload["first_name"] = "John"
    base_payload["last_name"] = "  \t \n "
    res2 = client.post("/api/v1/patients", json=base_payload)
    assert res2.status_code == 422


def test_create_patient_single_character_name_rejected(client: TestClient):
    """Rejects single-character first or last names."""
    payload = {
        "first_name": "J",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "blood_group": "A+",
        "emergency_contact": "Jane Doe"
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 422
    assert "at least 2 characters" in str(res.json()).lower()

    payload["first_name"] = "John"
    payload["last_name"] = " D "
    res2 = client.post("/api/v1/patients", json=payload)
    assert res2.status_code == 422


def test_create_patient_numeric_name_rejected(client: TestClient):
    """Rejects numeric-only names."""
    payload = {
        "first_name": "12345",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "blood_group": "A+",
        "emergency_contact": "Jane Doe"
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 422
    assert "cannot be numeric-only" in str(res.json()).lower()

    payload["first_name"] = "John"
    payload["last_name"] = "99"
    res2 = client.post("/api/v1/patients", json=payload)
    assert res2.status_code == 422


def test_create_patient_future_dob_rejected(client: TestClient):
    """Rejects dates of birth in the future."""
    payload = {
        "first_name": "Future",
        "last_name": "Person",
        "dob": "2099-12-31",
        "gender": "Male",
        "blood_group": "O+",
        "emergency_contact": "Jane Doe"
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 422
    assert "cannot be in the future" in str(res.json()).lower()


def test_create_patient_invalid_dob_format_rejected(client: TestClient):
    """Rejects invalid date strings or impossible calendar dates."""
    for bad_dob in ["not-a-date", "2020-02-31", "1990/01/01", "01-01-1990", ""]:
        payload = {
            "first_name": "Invalid",
            "last_name": "Date",
            "dob": bad_dob,
            "gender": "Male",
            "blood_group": "O+",
            "emergency_contact": "Jane Doe"
        }
        res = client.post("/api/v1/patients", json=payload)
        assert res.status_code == 422, f"Failed to reject invalid dob: {bad_dob}"


def test_create_patient_invalid_phone_rejected(client: TestClient):
    """Rejects non-phone or short strings for contact_phone."""
    for bad_phone in ["abc", "123", "+1-abc-555", "too-short", "12345"]:
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "Male",
            "blood_group": "O+",
            "contact_phone": bad_phone,
            "emergency_contact": "Jane Doe"
        }
        res = client.post("/api/v1/patients", json=payload)
        assert res.status_code == 422, f"Failed to reject invalid phone: {bad_phone}"


def test_create_patient_valid_international_phone_accepted(client: TestClient):
    """Accepts various standard international phone number formats."""
    for good_phone in ["+1-555-0199", "+44 20 7946 0950", "+91-9876543210", "(555) 019-2834", "+15550199"]:
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "Male",
            "blood_group": "O+",
            "contact_phone": good_phone,
            "emergency_contact": "Jane Doe"
        }
        res = client.post("/api/v1/patients", json=payload)
        assert res.status_code == 201, f"Failed to accept valid phone: {good_phone}"


def test_create_patient_missing_emergency_contact_rejected(client: TestClient):
    """Rejects missing or empty emergency contact."""
    for bad_em in [None, "", "   ", "A", "12345"]:
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "Male",
            "blood_group": "O+"
        }
        if bad_em is not None:
            payload["emergency_contact"] = bad_em
        res = client.post("/api/v1/patients", json=payload)
        assert res.status_code == 422, f"Failed to reject bad emergency contact: {bad_em}"


def test_create_patient_emergency_contact_embedded_phone_validation(client: TestClient):
    """Validates phone number embedded inside emergency contact."""
    # Valid embedded phone
    valid_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "blood_group": "O+",
        "emergency_contact": "Jane Doe (+1-555-0198)"
    }
    res_valid = client.post("/api/v1/patients", json=valid_payload)
    assert res_valid.status_code == 201

    # Invalid embedded phone inside parentheses
    invalid_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "blood_group": "O+",
        "emergency_contact": "Jane Doe (123)"
    }
    res_inv = client.post("/api/v1/patients", json=invalid_payload)
    assert res_inv.status_code == 422
    assert "emergency contact phone" in str(res_inv.json()).lower()


def test_create_patient_invalid_gender_rejected(client: TestClient):
    """Rejects genders outside Male, Female, Other."""
    for bad_gender in ["Alien", "Unknown", "X", "123"]:
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": bad_gender,
            "blood_group": "O+",
            "emergency_contact": "Jane Doe"
        }
        res = client.post("/api/v1/patients", json=payload)
        assert res.status_code == 422, f"Failed to reject bad gender: {bad_gender}"
        assert "supported options" in str(res.json()).lower()


def test_create_patient_invalid_blood_group_rejected(client: TestClient):
    """Rejects blood groups outside the 8 standard ABO/Rh groups."""
    for bad_bg in ["C+", "XYZ", "O", "AB", "Positive", "None"]:
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "Male",
            "blood_group": bad_bg,
            "emergency_contact": "Jane Doe"
        }
        res = client.post("/api/v1/patients", json=payload)
        assert res.status_code == 422, f"Failed to reject bad blood group: {bad_bg}"
        assert "supported options" in str(res.json()).lower()


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
