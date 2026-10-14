"""
Pytest Test Fixtures and Mock Database Injection
=================================================
Configures a comprehensive mock DatabaseManager so tests run 100% offline without live Neo4j
writes or live credentials, testing all FastAPI endpoints, serialization, and status codes.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from backend.app.database import DatabaseManager, get_db


class MockSummary:
    def __init__(self, result_available_after=2):
        self.result_available_after = result_available_after


class MockDatabaseManager:
    """Mock database that returns pre-configured records and intercepts Cypher queries."""

    def __init__(self, connected: bool = True):
        self._connected = connected
        self.executed_queries: List[Dict[str, Any]] = []
        self.custom_responses: Dict[str, List[Dict[str, Any]]] = {}

    def is_connected(self) -> bool:
        return self._connected

    def set_connected(self, status: bool):
        self._connected = status

    def set_query_response(self, query_snippet: str, response: List[Dict[str, Any]]):
        self.custom_responses[query_snippet] = response

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        read_only: bool = True
    ):
        params = parameters or {}
        self.executed_queries.append({"query": query, "params": params, "read_only": read_only})
        q_lower = query.lower()

        # Check user-registered custom responses first
        for snippet, resp in self.custom_responses.items():
            if snippet.lower() in q_lower:
                return resp, MockSummary()

        # 1. Encounter Count Safety Checks (Safe Deletion)
        if "encounter_count" in q_lower:
            if params.get("patient_id") == "P_HAS_ENCOUNTERS":
                return [{"encounter_count": 3}], MockSummary()
            if params.get("doctor_id") == "DOC_HAS_CASES":
                return [{"encounter_count": 2}], MockSummary()
            return [{"encounter_count": 0}], MockSummary()

        # 2. General Count Aggregations
        if "count(p) as total" in q_lower or "count(p)" in q_lower:
            return [{"total": 1}], MockSummary()
        if "count(d) as total" in q_lower or "count(d)" in q_lower:
            return [{"total": 1}], MockSummary()
        if "count(e) as total" in q_lower or "count(e)" in q_lower:
            return [{"total": 1}], MockSummary()

        # 3. Check for Duplicate IDs (Returns row ONLY if ID is known duplicate)
        if "return p.patient_id as pid" in q_lower:
            pid = params.get("pid")
            if pid == "EXISTING_P1001":
                return [{"pid": "EXISTING_P1001"}], MockSummary()
            # For encounter verification of patient existence:
            if "p_check" in query or "pid" in params and params["pid"] == "P1001":
                return [{"pid": "P1001"}], MockSummary()
            return [], MockSummary()

        if "return d.doctor_id as did" in q_lower:
            did = params.get("did") or params.get("doc_id")
            if did == "EXISTING_DOC":
                return [{"did": "EXISTING_DOC"}], MockSummary()
            if did == "DOC101":
                return [{"did": "DOC101"}], MockSummary()
            return [], MockSummary()

        # 4. Create Doctor
        if "create (d:doctor" in q_lower:
            return [{
                "doctor_id": params.get("doctor_id", "DOC101"),
                "first_name": params.get("first_name", "Arun"),
                "last_name": params.get("last_name", "Sharma"),
                "specialty": params.get("specialty", "Cardiology"),
                "license_number": params.get("license_number", "MD-101"),
                "email": params.get("email", ""),
                "phone": params.get("phone", ""),
                "years_of_experience": params.get("years_of_experience", 5),
                "department_id": params.get("department_id", "DEP01"),
                "department_name": "Cardiology"
            }], MockSummary()

        # 5. Create Patient
        if "create (p:patient" in q_lower:
            return [{
                "patient_id": params.get("patient_id", "P1001"),
                "first_name": params.get("first_name", "Fictional"),
                "last_name": params.get("last_name", "Patient"),
                "dob": params.get("dob", "1990-01-01"),
                "gender": params.get("gender", "Female"),
                "blood_group": params.get("blood_group", "O+"),
                "contact_phone": params.get("contact_phone", ""),
                "emergency_contact": params.get("emergency_contact", ""),
                "created_at": "2026-10-15T00:00:00Z"
            }], MockSummary()

        # 6. Create Encounter
        if "create (e:encounter" in q_lower:
            return [{"encounter_id": params.get("encounter_id", "ENC7001")}], MockSummary()

        # 7. Single Encounter Fetch
        if "encounter_id: $encounter_id" in q_lower:
            if params.get("encounter_id") == "ENC_NONEXISTENT":
                return [], MockSummary()
            return [{
                "encounter_id": params.get("encounter_id", "ENC7001"),
                "encounter_type": "Inpatient",
                "status": "Active",
                "start_time": "2026-10-15T08:00:00Z",
                "end_time": None,
                "reason_for_visit": "Chest pain workup",
                "clinical_record_raw": '{"vital_signs":{"temperature_celsius":37.2,"heart_rate_bpm":76,"blood_pressure":{"systolic_mmhg":120,"diastolic_mmhg":80},"respiratory_rate_bpm":16,"oxygen_saturation_percent":98},"clinical_notes":{"chief_complaint":"Chest discomfort","assessment_and_plan":"Observation"}}',
                "patient_id": "P1001",
                "patient_name": "Fictional Patient",
                "doctor_id": "DOC101",
                "doctor_name": "Arun Sharma",
                "department_name": "Cardiology",
                "room_number": "ICU-301",
                "diagnoses": [{"code": "I10", "name": "Hypertension", "status": "Primary"}],
                "prescriptions": [{"name": "Aspirin", "dosage": "81mg", "frequency": "Daily"}]
            }], MockSummary()

        # 8. Single Patient Fetch
        if "patient_id: $patient_id" in q_lower and "has_encounter" not in q_lower:
            if params.get("patient_id") == "P_NONEXISTENT":
                return [], MockSummary()
            return [{
                "patient_id": params.get("patient_id", "P1001"),
                "first_name": "Fictional",
                "last_name": "Patient",
                "dob": "1985-06-15",
                "gender": "Female",
                "blood_group": "A+",
                "contact_phone": "+1-555-1001",
                "emergency_contact": "Family Contact",
                "created_at": "2026-10-01T00:00:00Z"
            }], MockSummary()

        # 9. Patient Longitudinal History
        if "has_encounter" in q_lower and "patient_id: $patient_id" in q_lower:
            return [{
                "encounter_id": "ENC7001",
                "encounter_type": "Inpatient",
                "status": "Active",
                "start_time": "2026-10-15T08:00:00Z",
                "end_time": None,
                "reason_for_visit": "Chest pain workup",
                "clinical_record_raw": '{"vital_signs":{"temperature_celsius":37.2,"heart_rate_bpm":76,"blood_pressure":{"systolic_mmhg":120,"diastolic_mmhg":80},"respiratory_rate_bpm":16,"oxygen_saturation_percent":98},"clinical_notes":{"chief_complaint":"Chest discomfort","assessment_and_plan":"Observation"}}',
                "doctor_id": "DOC101",
                "doctor_name": "Arun Sharma",
                "department_name": "Cardiology",
                "room_number": "ICU-301",
                "diagnoses": [{"diagnosis_id": "DIAG-I10", "code": "I10", "name": "Hypertension", "status": "Primary"}],
                "prescriptions": [{"medication_id": "MED-ASPI", "name": "Aspirin", "dosage": "81mg", "frequency": "Daily"}]
            }], MockSummary()

        # 10. Single Doctor Fetch
        if "doctor_id: $doctor_id" in q_lower:
            if params.get("doctor_id") == "DOC_NONEXISTENT":
                return [], MockSummary()
            return [{
                "doctor_id": params.get("doctor_id", "DOC101"),
                "first_name": "Arun",
                "last_name": "Sharma",
                "specialty": "Cardiology",
                "license_number": "MD-CARD-101",
                "email": "a.sharma@hospital.org",
                "phone": "+1-555-0101",
                "years_of_experience": 14,
                "department_id": "DEP01",
                "department_name": "Cardiology"
            }], MockSummary()

        # 11. Single Department Fetch
        if "department_id: $department_id" in q_lower:
            if params.get("department_id") == "DEP_NONEXISTENT":
                return [], MockSummary()
            return [{
                "department_id": params.get("department_id", "DEP01"),
                "name": "Cardiology",
                "building": "Main Wing",
                "floor": 3,
                "phone_extension": "x3010",
                "doctor_count": 2
            }], MockSummary()

        # 12. Single Room Fetch
        if "room_id: $room_id" in q_lower:
            if params.get("room_id") == "RM_NONEXISTENT":
                return [], MockSummary()
            return [{
                "room_id": params.get("room_id", "RM-ICU-301"),
                "room_number": "ICU-301",
                "room_type": "ICU",
                "capacity": 1,
                "floor": 3,
                "current_occupancy": 1,
                "is_available": False
            }], MockSummary()

        # 13. List Patients Query
        if "match (p:patient)" in q_lower and "return p.patient_id as patient_id" in q_lower:
            return [{
                "patient_id": "P1001",
                "first_name": "Fictional",
                "last_name": "Patient",
                "dob": "1985-06-15",
                "gender": "Female",
                "blood_group": "A+",
                "contact_phone": "+1-555-1001",
                "emergency_contact": "Family Contact",
                "created_at": "2026-10-01T00:00:00Z"
            }], MockSummary()

        # 14. List Doctors Query
        if "match (d:doctor)" in q_lower and "return d.doctor_id as doctor_id" in q_lower:
            return [{
                "doctor_id": "DOC101",
                "first_name": "Arun",
                "last_name": "Sharma",
                "specialty": "Cardiology",
                "license_number": "MD-CARD-101",
                "email": "a.sharma@hospital.org",
                "phone": "+1-555-0101",
                "years_of_experience": 14,
                "department_id": "DEP01",
                "department_name": "Cardiology"
            }], MockSummary()

        # 15. Room Occupancy Analytics
        if "room_type" in q_lower and "current_occupants" in q_lower:
            return [{
                "room_id": "RM-ICU-301",
                "room_number": "ICU-301",
                "room_type": "ICU",
                "capacity": 1,
                "floor": 3,
                "current_occupants": 1,
                "is_available": False,
                "current_patients": [{"patient_id": "P1001", "patient_name": "Fictional Patient"}]
            }], MockSummary()

        # Default Fallback Record with complete schema fields
        return [{
            "patient_id": params.get("patient_id", "P1001"),
            "doctor_id": params.get("doctor_id", "DOC101"),
            "encounter_id": params.get("encounter_id", "ENC7001"),
            "room_id": params.get("room_id", "RM-ICU-301"),
            "department_id": params.get("department_id", "DEP01"),
            "first_name": "Fictional",
            "last_name": "Record",
            "patient_name": "Fictional Patient",
            "doctor_name": "Arun Sharma",
            "department_name": "Cardiology",
            "room_number": "ICU-301",
            "encounter_type": "Inpatient",
            "status": "Active",
            "start_time": "2026-10-15T08:00:00Z",
            "end_time": None,
            "reason_for_visit": "Chest pain workup",
            "dob": "1990-01-01",
            "gender": "Female",
            "blood_group": "A+",
            "contact_phone": "+1-555-0000",
            "emergency_contact": "Emergency",
            "created_at": "2026-10-01T00:00:00Z",
            "name": "General Department",
            "specialty": "Internal Medicine",
            "license_number": "MD-TEST-99",
            "capacity": 2,
            "floor": 1,
            "current_occupants": 1,
            "current_occupancy": 1,
            "is_available": True,
            "patient_count": 20,
            "doctor_count": 8,
            "department_count": 4,
            "encounter_count": 35,
            "active_admissions": 7,
            "total_rooms": 15,
            "query_time_ms": 2,
            "diagnoses": [],
            "prescriptions": []
        }], MockSummary()


@pytest.fixture
def mock_db() -> MockDatabaseManager:
    return MockDatabaseManager()


@pytest.fixture
def client(mock_db: MockDatabaseManager) -> TestClient:
    """Provides a TestClient with dependency override for get_db."""
    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
