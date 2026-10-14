"""
Patient Service
===============
Business logic and Cypher operations for Patient management, safe deletion,
and complete longitudinal clinical history retrieval.
"""

import json
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from backend.app.database import DatabaseManager
from backend.app.models.patient import PatientCreate, PatientUpdate


class PatientService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def list_patients(self, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> Dict[str, Any]:
        """Lists patients with optional search by full name, with pagination."""
        if search:
            query = """
            MATCH (p:Patient)
            WHERE toLower(p.first_name + ' ' + p.last_name) CONTAINS toLower($search)
               OR toLower(p.patient_id) CONTAINS toLower($search)
            RETURN p.patient_id AS patient_id,
                   p.first_name AS first_name,
                   p.last_name AS last_name,
                   p.dob AS dob,
                   p.gender AS gender,
                   p.blood_group AS blood_group,
                   p.contact_phone AS contact_phone,
                   p.emergency_contact AS emergency_contact,
                   p.created_at AS created_at
            ORDER BY p.patient_id ASC
            SKIP $skip LIMIT $limit
            """
            count_query = """
            MATCH (p:Patient)
            WHERE toLower(p.first_name + ' ' + p.last_name) CONTAINS toLower($search)
               OR toLower(p.patient_id) CONTAINS toLower($search)
            RETURN count(p) AS total
            """
            params = {"search": search, "skip": skip, "limit": limit}
        else:
            query = """
            MATCH (p:Patient)
            RETURN p.patient_id AS patient_id,
                   p.first_name AS first_name,
                   p.last_name AS last_name,
                   p.dob AS dob,
                   p.gender AS gender,
                   p.blood_group AS blood_group,
                   p.contact_phone AS contact_phone,
                   p.emergency_contact AS emergency_contact,
                   p.created_at AS created_at
            ORDER BY p.patient_id ASC
            SKIP $skip LIMIT $limit
            """
            count_query = "MATCH (p:Patient) RETURN count(p) AS total"
            params = {"skip": skip, "limit": limit}

        records, _ = self.db.execute_query(query, params)
        total_records, _ = self.db.execute_query(count_query, {"search": search} if search else {})
        total = total_records[0]["total"] if total_records else len(records)

        return {"total": total, "skip": skip, "limit": limit, "items": records}

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        """Retrieves a single patient by ID."""
        query = """
        MATCH (p:Patient {patient_id: $patient_id})
        RETURN p.patient_id AS patient_id,
               p.first_name AS first_name,
               p.last_name AS last_name,
               p.dob AS dob,
               p.gender AS gender,
               p.blood_group AS blood_group,
               p.contact_phone AS contact_phone,
               p.emergency_contact AS emergency_contact,
               p.created_at AS created_at
        """
        records, _ = self.db.execute_query(query, {"patient_id": patient_id})
        if not records:
            raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")
        return records[0]

    def create_patient(self, payload: PatientCreate) -> Dict[str, Any]:
        """Creates a new Patient node with unique patient_id."""
        pid = payload.patient_id or f"P{str(uuid4())[:8].upper()}"

        # Check existing
        existing, _ = self.db.execute_query(
            "MATCH (p:Patient {patient_id: $pid}) RETURN p.patient_id AS pid",
            {"pid": pid}
        )
        if existing:
            raise HTTPException(status_code=409, detail=f"Patient with ID '{pid}' already exists.")

        created_at = datetime.now(timezone.utc).isoformat()
        query = """
        CREATE (p:Patient {
            patient_id: $patient_id,
            first_name: $first_name,
            last_name: $last_name,
            dob: $dob,
            gender: $gender,
            blood_group: $blood_group,
            contact_phone: $contact_phone,
            emergency_contact: $emergency_contact,
            created_at: $created_at
        })
        RETURN p.patient_id AS patient_id,
               p.first_name AS first_name,
               p.last_name AS last_name,
               p.dob AS dob,
               p.gender AS gender,
               p.blood_group AS blood_group,
               p.contact_phone AS contact_phone,
               p.emergency_contact AS emergency_contact,
               p.created_at AS created_at
        """
        params = {
            "patient_id": pid,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "dob": payload.dob,
            "gender": payload.gender,
            "blood_group": payload.blood_group,
            "contact_phone": payload.contact_phone or "",
            "emergency_contact": payload.emergency_contact or "",
            "created_at": created_at
        }
        records, _ = self.db.execute_query(query, params, read_only=False)
        return records[0]

    def update_patient(self, patient_id: str, payload: PatientUpdate) -> Dict[str, Any]:
        """Updates patient demographic fields."""
        # Check existence first
        self.get_patient(patient_id)

        update_fields = []
        params: Dict[str, Any] = {"patient_id": patient_id}
        for field, val in payload.model_dump(exclude_unset=True).items():
            if val is not None:
                update_fields.append(f"p.{field} = ${field}")
                params[field] = val

        if not update_fields:
            return self.get_patient(patient_id)

        query = f"""
        MATCH (p:Patient {{patient_id: $patient_id}})
        SET {", ".join(update_fields)}
        RETURN p.patient_id AS patient_id,
               p.first_name AS first_name,
               p.last_name AS last_name,
               p.dob AS dob,
               p.gender AS gender,
               p.blood_group AS blood_group,
               p.contact_phone AS contact_phone,
               p.emergency_contact AS emergency_contact,
               p.created_at AS created_at
        """
        records, _ = self.db.execute_query(query, params, read_only=False)
        return records[0]

    def delete_patient(self, patient_id: str) -> Dict[str, str]:
        """
        Safe deletion: Rejects deletion if active or historical encounters exist.
        Never cascade-deletes medical history silently.
        """
        self.get_patient(patient_id)

        # Check for clinical encounters
        check_query = """
        MATCH (p:Patient {patient_id: $patient_id})-[:HAS_ENCOUNTER]->(e:Encounter)
        RETURN count(e) AS encounter_count
        """
        records, _ = self.db.execute_query(check_query, {"patient_id": patient_id})
        count = records[0]["encounter_count"] if records else 0
        if count > 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Patient '{patient_id}' has {count} active or historical clinical encounters. "
                    "Deletion refused by hospital safety protocol to prevent loss of clinical history."
                )
            )

        delete_query = """
        MATCH (p:Patient {patient_id: $patient_id})
        DETACH DELETE p
        """
        self.db.execute_query(delete_query, {"patient_id": patient_id}, read_only=False)
        return {"status": "deleted", "patient_id": patient_id}

    def get_patient_history(self, patient_id: str) -> Dict[str, Any]:
        """Returns complete clinical encounter timeline, doctors, diagnoses, and prescriptions."""
        patient = self.get_patient(patient_id)

        query = """
        MATCH (p:Patient {patient_id: $patient_id})-[:HAS_ENCOUNTER]->(e:Encounter)
        OPTIONAL MATCH (e)-[:ATTENDED_BY]->(doc:Doctor)-[:BELONGS_TO]->(dept:Department)
        OPTIONAL MATCH (e)-[r_diag:DIAGNOSED_WITH]->(diag:Diagnosis)
        OPTIONAL MATCH (e)-[r_med:PRESCRIBED]->(med:Medication)
        OPTIONAL MATCH (e)-[:ADMITTED_TO]->(rm:Room)
        RETURN e.encounter_id AS encounter_id,
               e.encounter_type AS encounter_type,
               e.status AS status,
               e.start_time AS start_time,
               e.end_time AS end_time,
               e.reason_for_visit AS reason_for_visit,
               e.clinical_record_json AS clinical_record_raw,
               doc.doctor_id AS doctor_id,
               doc.first_name + ' ' + doc.last_name AS doctor_name,
               dept.name AS department_name,
               rm.room_number AS room_number,
               collect(DISTINCT {
                   diagnosis_id: diag.diagnosis_id,
                   code: diag.icd10_code,
                   name: diag.name,
                   status: r_diag.status
               }) AS diagnoses,
               collect(DISTINCT {
                   medication_id: med.medication_id,
                   name: med.name,
                   dosage: r_med.dosage,
                   frequency: r_med.frequency
               }) AS prescriptions
        ORDER BY e.start_time DESC
        """
        records, _ = self.db.execute_query(query, {"patient_id": patient_id})

        encounters = []
        for r in records:
            clinical_record = None
            if r.get("clinical_record_raw"):
                try:
                    clinical_record = json.loads(r["clinical_record_raw"])
                except Exception:
                    clinical_record = {"raw": r["clinical_record_raw"]}

            diagnoses = [d for d in r.get("diagnoses", []) if d.get("diagnosis_id")]
            prescriptions = [p for p in r.get("prescriptions", []) if p.get("medication_id")]

            encounters.append({
                "encounter_id": r["encounter_id"],
                "encounter_type": r["encounter_type"],
                "status": r["status"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "reason_for_visit": r["reason_for_visit"],
                "doctor": {"id": r["doctor_id"], "name": r["doctor_name"], "department": r["department_name"]},
                "room": r["room_number"],
                "diagnoses": diagnoses,
                "prescriptions": prescriptions,
                "clinical_record": clinical_record
            })

        return {
            "patient": patient,
            "total_encounters": len(encounters),
            "encounters": encounters
        }
