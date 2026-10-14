"""
Clinical Encounter and Document Model Tests
===========================================
Verifies Encounter logging, embedded JSON clinical record validation,
vital sign range constraints, and inpatient discharge updates.
"""

from fastapi.testclient import TestClient


def test_create_encounter_with_valid_document_record(client: TestClient):
    """Verifies creating an encounter with full embedded JSON clinical record."""
    payload = {
        "patient_id": "P1001",
        "doctor_id": "DOC101",
        "encounter_type": "Inpatient",
        "status": "Active",
        "start_time": "2026-10-15T09:00:00Z",
        "reason_for_visit": "Acute respiratory distress and fever",
        "room_id": "RM-ICU-301",
        "clinical_record": {
            "vital_signs": {
                "temperature_celsius": 38.2,
                "heart_rate_bpm": 102,
                "blood_pressure": {
                    "systolic_mmhg": 130,
                    "diastolic_mmhg": 84
                },
                "respiratory_rate_bpm": 20,
                "oxygen_saturation_percent": 95,
                "recorded_at": "2026-10-15T09:15:00Z"
            },
            "clinical_notes": {
                "chief_complaint": "Dyspnea and productive cough for 3 days",
                "assessment_and_plan": "Community-acquired pneumonia. Supplemental O2 ordered."
            }
        }
    }
    res = client.post("/api/v1/encounters", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["encounter_type"] == "Inpatient"
    assert data["status"] == "Active"


def test_create_encounter_rejects_invalid_vitals(client: TestClient):
    """Verifies Pydantic rejects physiologically impossible vital signs (e.g., negative or extreme values)."""
    payload = {
        "patient_id": "P1001",
        "doctor_id": "DOC101",
        "encounter_type": "Outpatient",
        "start_time": "2026-10-15T10:00:00Z",
        "reason_for_visit": "Checkup",
        "clinical_record": {
            "vital_signs": {
                "temperature_celsius": 55.0,  # Extreme fever impossible in humans
                "heart_rate_bpm": -10,        # Negative heart rate invalid
                "blood_pressure": {
                    "systolic_mmhg": 10,      # Systolic too low (< 50)
                    "diastolic_mmhg": 80
                },
                "respiratory_rate_bpm": 16,
                "oxygen_saturation_percent": 150 # Cannot exceed 100%
            },
            "clinical_notes": {
                "chief_complaint": "Invalid vitals test",
                "assessment_and_plan": "Testing"
            }
        }
    }
    res = client.post("/api/v1/encounters", json=payload)
    assert res.status_code == 422  # Unprocessable Entity


def test_update_encounter_status_and_discharge(client: TestClient):
    """Verifies updating encounter status to Discharged with discharge timestamp."""
    payload = {
        "status": "Discharged",
        "end_time": "2026-10-18T12:00:00Z"
    }
    res = client.put("/api/v1/encounters/ENC7001", json=payload)
    assert res.status_code == 200


def test_get_encounter_details(client: TestClient):
    """Verifies retrieving an encounter and parsing its embedded clinical record."""
    res = client.get("/api/v1/encounters/ENC7001")
    assert res.status_code == 200
    data = res.json()
    assert data["encounter_id"] == "ENC7001"
    assert "clinical_record" in data
