"""
Doctor Service
==============
Business logic and Cypher operations for Doctor management and Department affiliations.
"""

from uuid import uuid4
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from backend.app.database import DatabaseManager
from backend.app.models.doctor import DoctorCreate, DoctorUpdate


class DoctorService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def list_doctors(
        self,
        skip: int = 0,
        limit: int = 50,
        specialty: Optional[str] = None,
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lists doctors with optional specialty and department filters."""
        where_clauses = []
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if specialty:
            where_clauses.append("toLower(d.specialty) = toLower($specialty)")
            params["specialty"] = specialty

        if department_id:
            where_clauses.append("dept.department_id = $department_id")
            params["department_id"] = department_id

        where_stmt = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
        MATCH (d:Doctor)
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(dept:Department)
        {where_stmt}
        RETURN d.doctor_id AS doctor_id,
               d.first_name AS first_name,
               d.last_name AS last_name,
               d.specialty AS specialty,
               d.license_number AS license_number,
               d.email AS email,
               d.phone AS phone,
               d.years_of_experience AS years_of_experience,
               dept.department_id AS department_id,
               dept.name AS department_name
        ORDER BY d.doctor_id ASC
        SKIP $skip LIMIT $limit
        """

        count_query = f"""
        MATCH (d:Doctor)
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(dept:Department)
        {where_stmt}
        RETURN count(d) AS total
        """

        records, _ = self.db.execute_query(query, params)
        total_records, _ = self.db.execute_query(count_query, params)
        total = total_records[0]["total"] if total_records else len(records)

        return {"total": total, "skip": skip, "limit": limit, "items": records}

    def get_doctor(self, doctor_id: str) -> Dict[str, Any]:
        """Retrieves a single doctor by ID."""
        query = """
        MATCH (d:Doctor {doctor_id: $doctor_id})
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(dept:Department)
        RETURN d.doctor_id AS doctor_id,
               d.first_name AS first_name,
               d.last_name AS last_name,
               d.specialty AS specialty,
               d.license_number AS license_number,
               d.email AS email,
               d.phone AS phone,
               d.years_of_experience AS years_of_experience,
               dept.department_id AS department_id,
               dept.name AS department_name
        """
        records, _ = self.db.execute_query(query, {"doctor_id": doctor_id})
        if not records:
            raise HTTPException(status_code=404, detail=f"Doctor '{doctor_id}' not found.")
        return records[0]

    def create_doctor(self, payload: DoctorCreate) -> Dict[str, Any]:
        """Creates a Doctor node and creates BELONGS_TO relationship if department provided."""
        doc_id = payload.doctor_id or f"DOC{str(uuid4())[:6].upper()}"

        existing, _ = self.db.execute_query(
            "MATCH (d:Doctor {doctor_id: $doc_id}) RETURN d.doctor_id AS did",
            {"doc_id": doc_id}
        )
        if existing:
            raise HTTPException(status_code=409, detail=f"Doctor with ID '{doc_id}' already exists.")

        create_query = """
        CREATE (d:Doctor {
            doctor_id: $doctor_id,
            first_name: $first_name,
            last_name: $last_name,
            specialty: $specialty,
            license_number: $license_number,
            email: $email,
            phone: $phone,
            years_of_experience: $years_of_experience
        })
        WITH d
        OPTIONAL MATCH (dept:Department {department_id: $department_id})
        FOREACH (_ IN CASE WHEN dept IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:BELONGS_TO]->(dept)
        )
        RETURN d.doctor_id AS doctor_id,
               d.first_name AS first_name,
               d.last_name AS last_name,
               d.specialty AS specialty,
               d.license_number AS license_number,
               d.email AS email,
               d.phone AS phone,
               d.years_of_experience AS years_of_experience,
               dept.department_id AS department_id,
               dept.name AS department_name
        """
        params = {
            "doctor_id": doc_id,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "specialty": payload.specialty,
            "license_number": payload.license_number,
            "email": payload.email or "",
            "phone": payload.phone or "",
            "years_of_experience": payload.years_of_experience or 0,
            "department_id": payload.department_id or ""
        }
        records, _ = self.db.execute_query(create_query, params, read_only=False)
        return records[0]

    def update_doctor(self, doctor_id: str, payload: DoctorUpdate) -> Dict[str, Any]:
        """Updates doctor details and re-assigns department if changed."""
        self.get_doctor(doctor_id)

        update_fields = []
        params: Dict[str, Any] = {"doctor_id": doctor_id}
        data = payload.model_dump(exclude_unset=True)

        for field in ["first_name", "last_name", "specialty", "email", "phone", "years_of_experience"]:
            if field in data and data[field] is not None:
                update_fields.append(f"d.{field} = ${field}")
                params[field] = data[field]

        set_clause = f"SET {', '.join(update_fields)}" if update_fields else ""

        dept_handling = ""
        if "department_id" in data:
            dept_id = data["department_id"]
            params["dept_id"] = dept_id or ""
            dept_handling = """
            WITH d
            OPTIONAL MATCH (d)-[r:BELONGS_TO]->(:Department)
            DELETE r
            WITH d
            OPTIONAL MATCH (new_dept:Department {department_id: $dept_id})
            FOREACH (_ IN CASE WHEN new_dept IS NOT NULL THEN [1] ELSE [] END |
                MERGE (d)-[:BELONGS_TO]->(new_dept)
            )
            """

        query = f"""
        MATCH (d:Doctor {{doctor_id: $doctor_id}})
        {set_clause}
        {dept_handling}
        WITH d
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(dept:Department)
        RETURN d.doctor_id AS doctor_id,
               d.first_name AS first_name,
               d.last_name AS last_name,
               d.specialty AS specialty,
               d.license_number AS license_number,
               d.email AS email,
               d.phone AS phone,
               d.years_of_experience AS years_of_experience,
               dept.department_id AS department_id,
               dept.name AS department_name
        """
        records, _ = self.db.execute_query(query, params, read_only=False)
        return records[0]

    def delete_doctor(self, doctor_id: str) -> Dict[str, str]:
        """Safe deletion: Rejects if physician is assigned to any encounters."""
        self.get_doctor(doctor_id)

        check_query = """
        MATCH (d:Doctor {doctor_id: $doctor_id})<-[:ATTENDED_BY]-(e:Encounter)
        RETURN count(e) AS encounter_count
        """
        records, _ = self.db.execute_query(check_query, {"doctor_id": doctor_id})
        count = records[0]["encounter_count"] if records else 0
        if count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Doctor '{doctor_id}' is assigned to {count} clinical encounters. Cannot delete."
            )

        self.db.execute_query(
            "MATCH (d:Doctor {doctor_id: $doctor_id}) DETACH DELETE d",
            {"doctor_id": doctor_id},
            read_only=False
        )
        return {"status": "deleted", "doctor_id": doctor_id}
