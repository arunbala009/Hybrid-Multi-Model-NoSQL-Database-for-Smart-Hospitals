"""
Frontend API Client Unit Tests
==============================
Validates HTTP request building, response handling, error capturing,
timeouts, and edge cases using mocked backend responses.
Zero live database writes or network calls.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock
from frontend.api_client import HospitalAPIClient


@pytest.fixture
def client():
    return HospitalAPIClient(base_url="http://testserver:8000")


# =============================================================================
# 1. Health Diagnostics
# =============================================================================
def test_check_health_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "database": "connected"}

    with patch("requests.request", return_value=mock_resp) as mock_req:
        res = client.check_health()
        assert res["success"] is True
        assert res["data"]["database"] == "connected"
        assert res["status_code"] == 200
        mock_req.assert_called_once_with(
            method="GET",
            url="http://testserver:8000/health",
            params=None,
            json=None,
            headers={"Accept": "application/json"},
            timeout=(5.0, 20.0)
        )


def test_check_health_connection_error(client):
    with patch("requests.request", side_effect=requests.exceptions.ConnectionError("Connection refused")):
        res = client.check_health()
        assert res["success"] is False
        assert "Cannot connect to backend API" in res["error"]
        assert res["status_code"] == 503


def test_check_health_timeout(client):
    with patch("requests.request", side_effect=requests.exceptions.Timeout("Read timeout")):
        res = client.check_health()
        assert res["success"] is False
        assert "timed out" in res["error"]
        assert res["status_code"] == 504


# =============================================================================
# 2. Patients API
# =============================================================================
def test_get_patients_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total": 1,
        "skip": 0,
        "limit": 10,
        "items": [{"patient_id": "P1001", "first_name": "John", "last_name": "Doe"}]
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_patients(skip=0, limit=10, search="John")
        assert res["success"] is True
        assert res["data"]["total"] == 1
        assert len(res["data"]["items"]) == 1


def test_get_patients_empty_results(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"total": 0, "skip": 0, "limit": 10, "items": []}

    with patch("requests.request", return_value=mock_resp):
        res = client.get_patients(skip=0, limit=10, search="Nonexistent")
        assert res["success"] is True
        assert res["data"]["total"] == 0
        assert res["data"]["items"] == []


def test_get_patient_not_found(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"detail": "Patient 'P9999' not found."}

    with patch("requests.request", return_value=mock_resp):
        res = client.get_patient("P9999")
        assert res["success"] is False
        assert res["status_code"] == 404
        assert "not found" in res["error"]


def test_create_patient_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {
        "patient_id": "P1001",
        "first_name": "Alice",
        "last_name": "Smith",
        "dob": "1990-01-01",
        "gender": "Female",
        "blood_group": "A+"
    }

    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "dob": "1990-01-01",
        "gender": "Female",
        "blood_group": "A+"
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.create_patient(payload)
        assert res["success"] is True
        assert res["data"]["patient_id"] == "P1001"


def test_create_patient_validation_error(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 422
    mock_resp.json.return_value = {"detail": "Field 'first_name' is required."}

    with patch("requests.request", return_value=mock_resp):
        res = client.create_patient({})
        assert res["success"] is False
        assert res["status_code"] == 422
        assert "required" in res["error"]


def test_delete_patient_blocked_by_safety(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 409
    mock_resp.json.return_value = {"detail": "Cannot delete patient with active admissions."}

    with patch("requests.request", return_value=mock_resp):
        res = client.delete_patient("P1001")
        assert res["success"] is False
        assert res["status_code"] == 409
        assert "active admissions" in res["error"]


# =============================================================================
# 3. Doctors & Departments API
# =============================================================================
def test_get_doctors_filtering(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total": 1,
        "items": [{"doctor_id": "DOC201", "specialty": "Cardiology", "department_id": "DEP01"}]
    }

    with patch("requests.request", return_value=mock_resp) as mock_req:
        res = client.get_doctors(specialty="Cardiology", department_id="DEP01")
        assert res["success"] is True
        assert len(res["data"]["items"]) == 1
        # verify query params passed
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["params"]["specialty"] == "Cardiology"
        assert call_kwargs["params"]["department_id"] == "DEP01"


def test_get_departments_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total": 2,
        "items": [
            {"department_id": "DEP01", "name": "Cardiology"},
            {"department_id": "DEP02", "name": "Neurology"}
        ]
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_departments()
        assert res["success"] is True
        assert res["data"]["total"] == 2


# =============================================================================
# 4. Rooms API
# =============================================================================
def test_get_rooms_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total": 1,
        "items": [{"room_id": "RM101", "room_type": "ICU", "capacity": 2, "current_occupancy": 1}]
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_rooms(room_type="ICU", floor=1)
        assert res["success"] is True
        assert res["data"]["items"][0]["room_type"] == "ICU"


# =============================================================================
# 5. Encounters API & Clinical Documents
# =============================================================================
def test_get_encounters_with_clinical_record(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total": 1,
        "items": [{
            "encounter_id": "ENC5001",
            "status": "Active",
            "clinical_record": {
                "vital_signs": {"temperature_celsius": 37.0, "heart_rate_bpm": 72}
            }
        }]
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_encounters(status="Active")
        assert res["success"] is True
        enc = res["data"]["items"][0]
        assert enc["clinical_record"]["vital_signs"]["heart_rate_bpm"] == 72


def test_update_encounter_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"encounter_id": "ENC5001", "status": "Discharged"}

    with patch("requests.request", return_value=mock_resp):
        res = client.update_encounter("ENC5001", {"status": "Discharged"})
        assert res["success"] is True
        assert res["data"]["status"] == "Discharged"


# =============================================================================
# 6. Analytics API
# =============================================================================
def test_get_overview_analytics(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total_patients": 20,
        "total_doctors": 8,
        "total_departments": 4,
        "total_encounters": 35,
        "active_admissions": 5,
        "total_rooms": 15
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_overview_analytics()
        assert res["success"] is True
        assert res["data"]["total_patients"] == 20


def test_get_treatment_pathways(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total_pathway_nodes": 2,
        "pathways": [
            {"patient_id": "P1001", "encounter_id": "ENC5001", "physician": "Dr. Smith"}
        ]
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_treatment_pathways(patient_id="P1001")
        assert res["success"] is True
        assert len(res["data"]["pathways"]) == 1


def test_get_room_sharing_analysis(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "disclaimer": "Simulated contact analysis...",
        "contact_pairs_count": 1,
        "overlapping_encounters": [
            {"room_number": "101", "patient_1_name": "Alice", "patient_2_name": "Bob"}
        ]
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_room_sharing()
        assert res["success"] is True
        assert res["data"]["contact_pairs_count"] == 1
        assert "Simulated" in res["data"]["disclaimer"]


# =============================================================================
# 7. Demo Seeding API
# =============================================================================
def test_demo_status(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "ready",
        "dataset_specification": {"total_patients": 20}
    }

    with patch("requests.request", return_value=mock_resp):
        res = client.get_demo_status()
        assert res["success"] is True
        assert res["data"]["dataset_specification"]["total_patients"] == 20


def test_demo_seed_dry_run_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "dry_run": True,
        "status": "validation_successful",
        "nodes_planned": 82
    }

    with patch("requests.request", return_value=mock_resp) as mock_req:
        res = client.seed_demo_data(token="valid-secret-token", dry_run=True)
        assert res["success"] is True
        assert res["data"]["dry_run"] is True
        # verify headers and params
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["headers"]["X-Demo-Token"] == "valid-secret-token"
        assert call_kwargs["params"]["dry_run"] == "true"


def test_demo_seed_unauthorized(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"detail": "Unauthorized: Invalid or missing demo administration token."}

    with patch("requests.request", return_value=mock_resp):
        res = client.seed_demo_data(token="bad-token", dry_run=True)
        assert res["success"] is False
        assert res["status_code"] == 401
        assert "Unauthorized" in res["error"]
