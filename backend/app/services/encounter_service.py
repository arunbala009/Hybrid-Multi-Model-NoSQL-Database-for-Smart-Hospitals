"""
Clinical Encounter Service
==========================
Business logic for patient admissions, outpatient visits, clinical notes updates,
and graph relationships to Patient, Doctor, Room, Diagnosis, and Medications.
"""

import json
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from backend.app.database import DatabaseManager
from backend.app.models.encounter import EncounterCreate, EncounterUpdate


class EncounterService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def list_encounters(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        encounter_type: Optional[str] = None,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lists encounters with multi-attribute filtering."""
        where_clauses = []
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            where_clauses.append("e.status = $status")
            params["status"] = status
        if encounter_type:
            where_clauses.append("e.encounter_type = $encounter_type")
            params["encounter_type"] = encounter_type
        if patient_id:
            where_clauses.append("p.patient_id = $patient_id")
            params["patient_id"] = patient_id

        where_stmt = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
        MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter)
        OPTIONAL MATCH (e)-[:ATTENDED_BY]->(d:Doctor)-[:BELONGS_TO]->(dept:Department)
        OPTIONAL MATCH (e)-[:ADMITTED_TO]->(rm:Room)
        {where_stmt}
        RETURN e.encounter_id AS encounter_id,
               e.encounter_type AS encounter_type,
               e.status AS status,
               e.start_time AS start_time,
               e.end_time AS end_time,
               e.reason_for_visit AS reason_for_visit,
               e.clinical_record_json AS clinical_record_raw,
               p.patient_id AS patient_id,
               p.first_name + ' ' + p.last_name AS patient_name,
               d.doctor_id AS doctor_id,
               d.first_name + ' ' + d.last_name AS doctor_name,
               dept.name AS department_name,
               rm.room_number AS room_number
        ORDER BY e.start_time DESC
        SKIP $skip LIMIT $limit
        """

        count_query = f"""
        MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter)
        OPTIONAL MATCH (e)-[:ATTENDED_BY]->(d:Doctor)-[:BELONGS_TO]->(dept:Department)
        OPTIONAL MATCH (e)-[:ADMITTED_TO]->(rm:Room)
        {where_stmt}
        RETURN count(e) AS total
        """

        records, _ = self.db.execute_query(query, params)
        total_records, _ = self.db.execute_query(count_query, params)
        total = total_records[0]["total"] if total_records else len(records)

        items = []
        for r in records:
            clinical_record = None
            if r.get("clinical_record_raw"):
                try:
                    clinical_record = json.loads(r["clinical_record_raw"])
                except Exception:
                    clinical_record = {"raw": r["clinical_record_raw"]}

            items.append({
                "encounter_id": r["encounter_id"],
                "patient_id": r["patient_id"],
                "patient_name": r["patient_name"],
                "doctor_id": r["doctor_id"] or "",
                "doctor_name": r["doctor_name"] or "",
                "department_name": r["department_name"] or "",
                "room_number": r["room_number"] or "",
                "encounter_type": r["encounter_type"],
                "status": r["status"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "reason_for_visit": r["reason_for_visit"],
                "clinical_record": clinical_record
            })

        return {"total": total, "skip": skip, "limit": limit, "items": items}

    def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
        """Retrieves full details of a single encounter including diagnoses and prescriptions."""
        query = """
        MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter {encounter_id: $encounter_id})
        OPTIONAL MATCH (e)-[:ATTENDED_BY]->(d:Doctor)-[:BELONGS_TO]->(dept:Department)
        OPTIONAL MATCH (e)-[:ADMITTED_TO]->(rm:Room)
        OPTIONAL MATCH (e)-[r_diag:DIAGNOSED_WITH]->(diag:Diagnosis)
        OPTIONAL MATCH (e)-[r_med:PRESCRIBED]->(med:Medication)
        RETURN e.encounter_id AS encounter_id,
               e.encounter_type AS encounter_type,
               e.status AS status,
               e.start_time AS start_time,
               e.end_time AS end_time,
               e.reason_for_visit AS reason_for_visit,
               e.clinical_record_json AS clinical_record_raw,
               p.patient_id AS patient_id,
               p.first_name + ' ' + p.last_name AS patient_name,
               d.doctor_id AS doctor_id,
               d.first_name + ' ' + d.last_name AS doctor_name,
               dept.name AS department_name,
               rm.room_number AS room_number,
               collect(DISTINCT {
                   code: diag.icd10_code,
                   name: diag.name,
                   status: r_diag.status
               }) AS diagnoses,
               collect(DISTINCT {
                   name: med.name,
                   dosage: r_med.dosage,
                   frequency: r_med.frequency
               }) AS prescriptions
        """
        records, _ = self.db.execute_query(query, {"encounter_id": encounter_id})
        if not records or not records[0].get("encounter_id"):
            raise HTTPException(status_code=404, detail=f"Encounter '{encounter_id}' not found.")

        r = records[0]
        clinical_record = None
        if r.get("clinical_record_raw"):
            try:
                clinical_record = json.loads(r["clinical_record_raw"])
            except Exception:
                clinical_record = {"raw": r["clinical_record_raw"]}

        diagnoses = [d for d in r.get("diagnoses", []) if d.get("name")]
        prescriptions = [p for p in r.get("prescriptions", []) if p.get("name")]

        return {
            "encounter_id": r["encounter_id"],
            "patient_id": r["patient_id"],
            "patient_name": r["patient_name"],
            "doctor_id": r["doctor_id"] or "",
            "doctor_name": r["doctor_name"] or "",
            "department_name": r["department_name"] or "",
            "room_number": r["room_number"] or "",
            "encounter_type": r["encounter_type"],
            "status": r["status"],
            "start_time": r["start_time"],
            "end_time": r["end_time"],
            "reason_for_visit": r["reason_for_visit"],
            "diagnoses": diagnoses,
            "prescriptions": prescriptions,
            "clinical_record": clinical_record
        }

    def create_encounter(self, payload: EncounterCreate) -> Dict[str, Any]:
        """Creates an encounter, links to Patient, Doctor, Room, and embeds clinical record JSON."""
        eid = payload.encounter_id or f"ENC{str(uuid4())[:6].upper()}"

        # Verify patient exists
        p_check, _ = self.db.execute_query(
            "MATCH (p:Patient {patient_id: $pid}) RETURN p.patient_id AS pid",
            {"pid": payload.patient_id}
        )
        if not p_check:
            raise HTTPException(status_code=404, detail=f"Patient '{payload.patient_id}' not found.")

        # Verify doctor exists
        d_check, _ = self.db.execute_query(
            "MATCH (d:Doctor {doctor_id: $did}) RETURN d.doctor_id AS did",
            {"did": payload.doctor_id}
        )
        if not d_check:
            raise HTTPException(status_code=404, detail=f"Doctor '{payload.doctor_id}' not found.")

        # Serialize document-style JSON
        clinical_json_str = ""
        if payload.clinical_record:
            clinical_json_str = payload.clinical_record.model_dump_json()

        query = """
        MATCH (p:Patient {patient_id: $patient_id})
        MATCH (d:Doctor {doctor_id: $doctor_id})
        CREATE (e:Encounter {
            encounter_id: $encounter_id,
            encounter_type: $encounter_type,
            status: $status,
            start_time: $start_time,
            end_time: $end_time,
            reason_for_visit: $reason_for_visit,
            clinical_record_json: $clinical_record_json
        })
        CREATE (p)-[:HAS_ENCOUNTER {created_at: $start_time}]->(e)
        CREATE (e)-[:ATTENDED_BY {role: 'Attending', assigned_at: $start_time}]->(d)
        WITH e, p, d
        OPTIONAL MATCH (rm:Room {room_id: $room_id})
        FOREACH (_ IN CASE WHEN rm IS NOT NULL THEN [1] ELSE [] END |
            CREATE (e)-[:ADMITTED_TO {admitted_at: $start_time, bed_number: 'Bed-1'}]->(rm)
        )
        RETURN e.encounter_id AS encounter_id
        """
        params = {
            "encounter_id": eid,
            "patient_id": payload.patient_id,
            "doctor_id": payload.doctor_id,
            "encounter_type": payload.encounter_type,
            "status": payload.status,
            "start_time": payload.start_time,
            "end_time": payload.end_time or "",
            "reason_for_visit": payload.reason_for_visit,
            "clinical_record_json": clinical_json_str,
            "room_id": payload.room_id or ""
        }
        self.db.execute_query(query, params, read_only=False)
        return self.get_encounter(eid)

    def update_encounter(self, encounter_id: str, payload: EncounterUpdate) -> Dict[str, Any]:
        """Updates encounter status, discharge time, room reassignment, or clinical record."""
        current = self.get_encounter(encounter_id)

        update_fields = []
        params: Dict[str, Any] = {"encounter_id": encounter_id}
        data = payload.model_dump(exclude_unset=True)

        if "status" in data and data["status"]:
            update_fields.append("e.status = $status")
            params["status"] = data["status"]

        if "end_time" in data:
            update_fields.append("e.end_time = $end_time")
            params["end_time"] = data["end_time"] or ""

        if "reason_for_visit" in data and data["reason_for_visit"]:
            update_fields.append("e.reason_for_visit = $reason_for_visit")
            params["reason_for_visit"] = data["reason_for_visit"]

        if "clinical_record" in data and data["clinical_record"]:
            clinical_json_str = payload.clinical_record.model_dump_json()
            update_fields.append("e.clinical_record_json = $clinical_record_json")
            params["clinical_record_json"] = clinical_json_str

        set_clause = f"SET {', '.join(update_fields)}" if update_fields else ""

        query = f"""
        MATCH (e:Encounter {{encounter_id: $encounter_id}})
        {set_clause}
        RETURN e.encounter_id AS encounter_id
        """
        self.db.execute_query(query, params, read_only=False)
        return self.get_encounter(encounter_id)
