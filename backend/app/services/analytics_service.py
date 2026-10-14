"""
Clinical and Operational Graph Analytics Service
=================================================
High-performance Cypher pattern matching queries for hospital metrics,
doctor workloads, room occupancy, treatment pathways, and cross-infection room sharing.
"""

from typing import Dict, Any, List, Optional
from backend.app.database import DatabaseManager


class AnalyticsService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_overview_analytics(self) -> Dict[str, Any]:
        """Calculates hospital aggregate KPIs across graph entities."""
        query = """
        CALL {
            MATCH (p:Patient) RETURN count(p) AS patient_count
        }
        CALL {
            MATCH (d:Doctor) RETURN count(d) AS doctor_count
        }
        CALL {
            MATCH (dept:Department) RETURN count(dept) AS department_count
        }
        CALL {
            MATCH (e:Encounter) RETURN count(e) AS encounter_count
        }
        CALL {
            MATCH (e:Encounter)
            WHERE e.status = 'Active' AND (e.end_time IS NULL OR e.end_time = '')
            RETURN count(e) AS active_admissions
        }
        CALL {
            MATCH (r:Room) RETURN count(r) AS total_rooms
        }
        RETURN patient_count, doctor_count, department_count, encounter_count, active_admissions, total_rooms
        """
        try:
            records, summary = self.db.execute_query(query)
            if records:
                row = records[0]
                query_time_ms = summary.result_available_after if hasattr(summary, "result_available_after") else 0
                return {
                    "total_patients": row.get("patient_count", 0),
                    "total_doctors": row.get("doctor_count", 0),
                    "total_departments": row.get("department_count", 0),
                    "total_encounters": row.get("encounter_count", 0),
                    "active_admissions": row.get("active_admissions", 0),
                    "total_rooms": row.get("total_rooms", 0),
                    "query_time_ms": query_time_ms
                }
        except Exception:
            pass

        # Fallback for empty or newly initialized databases
        return {
            "total_patients": 0,
            "total_doctors": 0,
            "total_departments": 0,
            "total_encounters": 0,
            "active_admissions": 0,
            "total_rooms": 0,
            "query_time_ms": 0
        }

    def get_doctor_workload(self) -> Dict[str, Any]:
        """Encounters handled per physician, department affiliation, and relative caseload."""
        query = """
        MATCH (d:Doctor)
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(dept:Department)
        OPTIONAL MATCH (d)<-[:ATTENDED_BY]-(e:Encounter)
        OPTIONAL MATCH (d)<-[:ATTENDED_BY]-(active_e:Encounter {status: 'Active'})
        RETURN d.doctor_id AS doctor_id,
               d.first_name + ' ' + d.last_name AS doctor_name,
               d.specialty AS specialty,
               coalesce(dept.name, 'Unassigned') AS department,
               count(DISTINCT e) AS total_encounters,
               count(DISTINCT active_e) AS active_patients
        ORDER BY total_encounters DESC, d.doctor_id ASC
        """
        records, summary = self.db.execute_query(query)
        query_time_ms = summary.result_available_after if hasattr(summary, "result_available_after") else 0
        return {
            "total_doctors_evaluated": len(records),
            "query_time_ms": query_time_ms,
            "items": records
        }

    def get_department_statistics(self) -> Dict[str, Any]:
        """Department staffing, patient encounter volumes, and clinical demand."""
        query = """
        MATCH (dept:Department)
        OPTIONAL MATCH (dept)<-[:BELONGS_TO]-(d:Doctor)
        OPTIONAL MATCH (d)<-[:ATTENDED_BY]-(e:Encounter)
        OPTIONAL MATCH (d)<-[:ATTENDED_BY]-(active_e:Encounter {status: 'Active'})
        RETURN dept.department_id AS department_id,
               dept.name AS department_name,
               dept.building AS building,
               dept.floor AS floor,
               count(DISTINCT d) AS total_physicians,
               count(DISTINCT e) AS total_encounters,
               count(DISTINCT active_e) AS active_cases
        ORDER BY total_encounters DESC
        """
        records, summary = self.db.execute_query(query)
        query_time_ms = summary.result_available_after if hasattr(summary, "result_available_after") else 0
        return {
            "departments": records,
            "total": len(records),
            "query_time_ms": query_time_ms
        }

    def get_room_occupancy(self) -> Dict[str, Any]:
        """
        Calculates current room utilization based strictly on Active encounters.
        Historical discharges are not counted as occupants.
        """
        query = """
        MATCH (r:Room)
        OPTIONAL MATCH (r)<-[adm:ADMITTED_TO]-(e:Encounter)
        WHERE e.status = 'Active' AND (e.end_time IS NULL OR e.end_time = '')
        OPTIONAL MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e)
        RETURN r.room_id AS room_id,
               r.room_number AS room_number,
               r.room_type AS room_type,
               r.capacity AS capacity,
               r.floor AS floor,
               count(DISTINCT e) AS current_occupants,
               CASE WHEN count(DISTINCT e) >= r.capacity THEN false ELSE true END AS is_available,
               collect(DISTINCT {
                   patient_id: p.patient_id,
                   patient_name: p.first_name + ' ' + p.last_name,
                   encounter_id: e.encounter_id,
                   admitted_at: e.start_time
               }) AS current_patients
        ORDER BY r.floor ASC, r.room_number ASC
        """
        records, summary = self.db.execute_query(query)
        query_time_ms = summary.result_available_after if hasattr(summary, "result_available_after") else 0

        occupied_rooms = sum(1 for r in records if r["current_occupants"] > 0)
        total_capacity = sum(r["capacity"] for r in records)
        total_occupants = sum(r["current_occupants"] for r in records)

        return {
            "total_rooms": len(records),
            "occupied_rooms": occupied_rooms,
            "total_bed_capacity": total_capacity,
            "current_bed_occupancy": total_occupants,
            "occupancy_rate_percent": round((total_occupants / total_capacity * 100), 1) if total_capacity else 0.0,
            "query_time_ms": query_time_ms,
            "rooms": records
        }

    def get_treatment_pathways(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Chronologically ordered encounter timeline and clinical trajectory."""
        where_stmt = "WHERE p.patient_id = $patient_id" if patient_id else ""
        params = {"patient_id": patient_id} if patient_id else {}

        query = f"""
        MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter)
        {where_stmt}
        OPTIONAL MATCH (e)-[:ATTENDED_BY]->(d:Doctor)-[:BELONGS_TO]->(dept:Department)
        OPTIONAL MATCH (e)-[:ADMITTED_TO]->(r:Room)
        OPTIONAL MATCH (e)-[r_diag:DIAGNOSED_WITH]->(diag:Diagnosis)
        OPTIONAL MATCH (e)-[r_med:PRESCRIBED]->(med:Medication)
        RETURN p.patient_id AS patient_id,
               p.first_name + ' ' + p.last_name AS patient_name,
               e.encounter_id AS encounter_id,
               e.encounter_type AS encounter_type,
               e.status AS status,
               e.start_time AS start_time,
               e.end_time AS end_time,
               e.reason_for_visit AS reason_for_visit,
               d.first_name + ' ' + d.last_name AS physician,
               dept.name AS department,
               r.room_number AS room_number,
               collect(DISTINCT diag.name) AS diagnoses,
               collect(DISTINCT med.name) AS medications
        ORDER BY p.patient_id ASC, e.start_time ASC
        LIMIT 100
        """
        records, summary = self.db.execute_query(query, params)
        query_time_ms = summary.result_available_after if hasattr(summary, "result_available_after") else 0
        return {
            "total_pathway_nodes": len(records),
            "query_time_ms": query_time_ms,
            "pathways": records
        }

    def get_room_sharing_analysis(self, room_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulated Contact Analysis:
        Identifies distinct patients whose inpatient stays in the same room overlapped temporally.
        Does NOT treat all patients who used the same room at completely disjoint times as contacts.
        """
        where_room = "AND r.room_id = $room_id" if room_id else ""
        params = {"room_id": room_id} if room_id else {}

        query = f"""
        MATCH (p1:Patient)-[:HAS_ENCOUNTER]->(e1:Encounter)-[adm1:ADMITTED_TO]->(r:Room)
        MATCH (p2:Patient)-[:HAS_ENCOUNTER]->(e2:Encounter)-[adm2:ADMITTED_TO]->(r)
        WHERE p1.patient_id < p2.patient_id {where_room}
          AND e1.start_time <= coalesce(e2.end_time, '9999-12-31')
          AND coalesce(e1.end_time, '9999-12-31') >= e2.start_time
        RETURN r.room_id AS room_id,
               r.room_number AS room_number,
               r.room_type AS room_type,
               p1.patient_id AS patient_1_id,
               p1.first_name + ' ' + p1.last_name AS patient_1_name,
               e1.encounter_id AS encounter_1_id,
               e1.start_time AS patient_1_admit,
               e1.end_time AS patient_1_discharge,
               p2.patient_id AS patient_2_id,
               p2.first_name + ' ' + p2.last_name AS patient_2_name,
               e2.encounter_id AS encounter_2_id,
               e2.start_time AS patient_2_admit,
               e2.end_time AS patient_2_discharge
        ORDER BY r.room_number ASC, e1.start_time ASC
        LIMIT 50
        """
        records, summary = self.db.execute_query(query, params)
        query_time_ms = summary.result_available_after if hasattr(summary, "result_available_after") else 0
        return {
            "disclaimer": (
                "Simulated contact-analysis demonstration. Temporal room overlap indicates "
                "potential epidemiological exposure proximity; not clinical proof of transmission."
            ),
            "contact_pairs_count": len(records),
            "query_time_ms": query_time_ms,
            "overlapping_encounters": records
        }
