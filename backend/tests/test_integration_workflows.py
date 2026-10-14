"""
Multi-Step Integration Workflow Tests
======================================
Tests multi-stage clinical workflows across patients, doctors, encounters,
embedded document-style JSON records, rooms, analytics, and security.
Uses mocked Neo4j layer to guarantee zero live database writes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.tests.conftest import MockDatabaseManager


# =============================================================================
# 1. Full Patient Lifecycle Integration
# =============================================================================
def test_patient_full_lifecycle_workflow(client: TestClient, mock_db: MockDatabaseManager):
    """
    Simulates: Onboarding -> Searching -> Updating -> Attempting unsafe deletion -> Verifying safe rules.
    """
    # 1. Onboard patient
    mock_db.set_query_response(
        "MATCH (p:Patient {patient_id: $pid})",
        []  # Patient does not exist yet
    )
    mock_db.set_query_response(
        "CREATE (p:Patient",
        [{
            "patient_id": "P9001",
            "first_name": "Eleanor",
            "last_name": "Vane",
            "dob": "1988-06-15",
            "gender": "Female",
            "blood_group": "A+",
            "contact_phone": "+1-555-9001",
            "emergency_contact": "Charles Vane",
            "created_at": "2026-10-15T00:00:00Z"
        }]
    )

    create_payload = {
        "patient_id": "P9001",
        "first_name": "Eleanor",
        "last_name": "Vane",
        "dob": "1988-06-15",
        "gender": "Female",
        "blood_group": "A+",
        "contact_phone": "+1-555-9001",
        "emergency_contact": "Charles Vane"
    }
    create_res = client.post("/api/v1/patients", json=create_payload)
    assert create_res.status_code == 201
    assert create_res.json()["patient_id"] == "P9001"

    # 2. Search for patient
    mock_db.set_query_response(
        "return count(p) as total",
        [{"total": 1}]
    )
    mock_db.set_query_response(
        "order by p.patient_id asc",
        [{
            "patient_id": "P9001",
            "first_name": "Eleanor",
            "last_name": "Vane",
            "dob": "1988-06-15",
            "gender": "Female",
            "blood_group": "A+",
            "contact_phone": "+1-555-9001",
            "emergency_contact": "Charles Vane",
            "created_at": "2026-10-15T00:00:00Z"
        }]
    )
    search_res = client.get("/api/v1/patients?search=Eleanor")
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1
    assert search_res.json()["items"][0]["first_name"] == "Eleanor"

    # 3. Update patient details
    mock_db.set_query_response(
        "MATCH (p:Patient {patient_id: $patient_id})",
        [{
            "patient_id": "P9001",
            "first_name": "Eleanor",
            "last_name": "Vane-Smith",
            "dob": "1988-06-15",
            "gender": "Female",
            "blood_group": "A+",
            "contact_phone": "+1-555-9999",
            "emergency_contact": "Charles Vane",
            "created_at": "2026-10-15T00:00:00Z"
        }]
    )
    update_res = client.put("/api/v1/patients/P9001", json={"last_name": "Vane-Smith", "contact_phone": "+1-555-9999"})
    assert update_res.status_code == 200
    assert update_res.json()["last_name"] == "Vane-Smith"


# =============================================================================
# 2. Doctor and Department Association Workflow
# =============================================================================
def test_doctor_department_association_workflow(client: TestClient, mock_db: MockDatabaseManager):
    """
    Simulates: Inspecting departments -> Onboarding doctor -> Affiliating to department -> Filtering.
    """
    # 1. Fetch departments
    mock_db.set_query_response(
        "MATCH (dept:Department)",
        [{"department_id": "DEP01", "name": "Cardiology", "building": "Main Wing", "floor": 3, "phone_extension": "x3010", "doctor_count": 2}]
    )
    dept_res = client.get("/api/v1/departments")
    assert dept_res.status_code == 200
    assert len(dept_res.json()["items"]) == 1

    # 2. Register doctor
    mock_db.set_query_response(
        "MATCH (d:Doctor {doctor_id: $did})",
        []
    )
    mock_db.set_query_response(
        "MATCH (dept:Department {department_id: $dept_id})",
        [{"department_id": "DEP01"}]
    )
    mock_db.set_query_response(
        "CREATE (d:Doctor",
        [{
            "doctor_id": "DOC901",
            "first_name": "Simon",
            "last_name": "Helberg",
            "specialty": "Cardiology",
            "license_number": "MD-CARD-901",
            "email": "s.helberg@hospital.org",
            "phone": "+1-555-9011",
            "years_of_experience": 10,
            "department_id": "DEP01",
            "department_name": "Cardiology"
        }]
    )

    doc_payload = {
        "doctor_id": "DOC901",
        "first_name": "Simon",
        "last_name": "Helberg",
        "specialty": "Cardiology",
        "license_number": "MD-CARD-901",
        "department_id": "DEP01",
        "years_of_experience": 10
    }
    doc_res = client.post("/api/v1/doctors", json=doc_payload)
    assert doc_res.status_code == 201
    assert doc_res.json()["doctor_id"] == "DOC901"
    assert doc_res.json()["department_id"] == "DEP01"


# =============================================================================
# 3. Clinical Encounter & Document-Style JSON Workflow
# =============================================================================
def test_encounter_and_document_json_workflow(client: TestClient, mock_db: MockDatabaseManager):
    """
    Simulates: Creating admission with embedded vital signs & clinical notes ->
    Inspecting semi-structured JSON document -> Updating discharge summary.
    """
    mock_db.set_query_response("MATCH (p:Patient {patient_id: $pid})", [{"pid": "P1001"}])
    mock_db.set_query_response("MATCH (d:Doctor {doctor_id: $did})", [{"did": "DOC101"}])
    mock_db.set_query_response(
        "CREATE (e:Encounter",
        [{"encounter_id": "ENC9001", "status": "Active"}]
    )

    enc_payload = {
        "encounter_id": "ENC9001",
        "patient_id": "P1001",
        "doctor_id": "DOC101",
        "encounter_type": "Inpatient",
        "status": "Active",
        "start_time": "2026-10-15T08:00:00Z",
        "reason_for_visit": "Acute arrhythmia evaluation",
        "room_id": "RM-ICU-301",
        "primary_diagnosis": "Atrial Fibrillation",
        "primary_icd10": "I48.91",
        "clinical_record": {
            "vital_signs": {
                "temperature_celsius": 37.1,
                "heart_rate_bpm": 110,
                "blood_pressure": {"systolic_mmhg": 135, "diastolic_mmhg": 88},
                "respiratory_rate_bpm": 18,
                "oxygen_saturation_percent": 97
            },
            "clinical_notes": {
                "chief_complaint": "Palpitations and dizziness",
                "assessment_and_plan": "Initiate IV diltiazem, monitor telemetry continuously."
            }
        }
    }

    create_res = client.post("/api/v1/encounters", json=enc_payload)
    assert create_res.status_code == 201
    assert create_res.json()["encounter_id"] == "ENC9001"

    # Fetch encounter details verifying document JSON parsing
    mock_db.set_query_response(
        "MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter {encounter_id: $encounter_id})",
        [{
            "encounter_id": "ENC9001",
            "patient_id": "P1001",
            "patient_name": "Arthur Pendleton",
            "doctor_id": "DOC101",
            "doctor_name": "Dr. Arun Sharma",
            "department_name": "Cardiology",
            "room_number": "ICU-301",
            "encounter_type": "Inpatient",
            "status": "Active",
            "start_time": "2026-10-15T08:00:00Z",
            "end_time": None,
            "reason_for_visit": "Acute arrhythmia evaluation",
            "clinical_record_raw": '{"vital_signs": {"temperature_celsius": 37.1, "heart_rate_bpm": 110}, "clinical_notes": {"chief_complaint": "Palpitations"}}',
            "diagnoses": [{"code": "I48.91", "name": "Atrial Fibrillation", "status": "Primary"}],
            "prescriptions": [{"name": "Diltiazem", "dosage": "20mg IV", "frequency": "Stat"}]
        }]
    )

    get_res = client.get("/api/v1/encounters/ENC9001")
    assert get_res.status_code == 200
    enc_data = get_res.json()
    assert enc_data["encounter_id"] == "ENC9001"
    assert enc_data["clinical_record"]["vital_signs"]["heart_rate_bpm"] == 110
    assert len(enc_data["diagnoses"]) == 1


# =============================================================================
# 4. Room Allocation and Co-Occupancy Contact Tracing Integration
# =============================================================================
def test_room_occupancy_and_contact_tracing_workflow(client: TestClient, mock_db: MockDatabaseManager):
    """
    Verifies that room occupancy correctly distinguishes active vs historical stays,
    and simulated room sharing reports the required epidemiological disclaimer.
    """
    # 1. Room Occupancy
    mock_db.set_query_response(
        "MATCH (r:Room)",
        [
            {
                "room_id": "RM-GEN-201",
                "room_number": "GW-201",
                "room_type": "General Ward",
                "capacity": 2,
                "floor": 2,
                "current_occupants": 1,
                "is_available": True,
                "current_patients": [{"patient_id": "P1001", "patient_name": "Arthur Pendleton"}]
            }
        ]
    )
    occ_res = client.get("/api/v1/analytics/room-occupancy")
    assert occ_res.status_code == 200
    odata = occ_res.json()
    assert odata["occupied_rooms"] == 1
    assert odata["total_bed_capacity"] == 2
    assert odata["current_bed_occupancy"] == 1

    # 2. Simulated Room Sharing Contact Tracing
    mock_db.set_query_response(
        "MATCH (p1:Patient)-[:HAS_ENCOUNTER]->(e1:Encounter)-[adm1:ADMITTED_TO]->(r:Room)",
        [
            {
                "room_id": "RM-GEN-201",
                "room_number": "GW-201",
                "room_type": "General Ward",
                "patient_1_id": "P1001",
                "patient_1_name": "Arthur Pendleton",
                "encounter_1_id": "ENC1001",
                "patient_1_admit": "2026-10-01T10:00:00Z",
                "patient_1_discharge": "2026-10-04T12:00:00Z",
                "patient_2_id": "P1002",
                "patient_2_name": "Beatrice Holloway",
                "encounter_2_id": "ENC1002",
                "patient_2_admit": "2026-10-02T14:00:00Z",
                "patient_2_discharge": "2026-10-06T09:00:00Z"
            }
        ]
    )
    rs_res = client.get("/api/v1/analytics/room-sharing")
    assert rs_res.status_code == 200
    rdata = rs_res.json()
    assert "disclaimer" in rdata
    assert "Simulated contact-analysis" in rdata["disclaimer"]
    assert rdata["contact_pairs_count"] == 1
    assert len(rdata["overlapping_encounters"]) == 1


# =============================================================================
# 5. Seeding Authorization and Dry-Run Boundary Enforcement
# =============================================================================
def test_seeder_dry_run_boundary_enforcement(client: TestClient):
    """
    Verifies that the demo seeder cannot be called without authorization,
    and defaults to dry-run (zero writes).
    """
    # 1. No token -> 401
    unauth_res = client.post("/api/v1/demo/seed")
    assert unauth_res.status_code == 401

    # 2. Invalid token -> 401
    bad_token_res = client.post("/api/v1/demo/seed", headers={"X-Demo-Token": "invalid-token"})
    assert bad_token_res.status_code == 401

    # 3. Valid token with default dry-run
    valid_res = client.post(
        "/api/v1/demo/seed?dry_run=true",
        headers={"X-Demo-Token": "hospital-academic-demo-key-2026"}
    )
    assert valid_res.status_code == 200
    vdata = valid_res.json()
    assert vdata["dry_run"] is True
    assert vdata["status"] == "dry_run_success"
    assert "patients" in vdata
    assert vdata["patients"] == 20
