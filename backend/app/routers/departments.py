"""
Departments API Router
======================
Endpoints for hospital divisions, clinical specialties, and facility locations.
"""

from fastapi import APIRouter, Depends, Path, HTTPException
from backend.app.database import DatabaseManager, get_db
from backend.app.models.department import DepartmentResponse, DepartmentListResponse

router = APIRouter(prefix="/api/v1/departments", tags=["Departments"])


@router.get("", response_model=DepartmentListResponse, summary="List Hospital Departments")
def list_departments(db: DatabaseManager = Depends(get_db)):
    """Retrieves all hospital departments along with physician headcount."""
    query = """
    MATCH (dept:Department)
    OPTIONAL MATCH (d:Doctor)-[:BELONGS_TO]->(dept)
    RETURN dept.department_id AS department_id,
           dept.name AS name,
           dept.building AS building,
           dept.floor AS floor,
           dept.phone_extension AS phone_extension,
           count(DISTINCT d) AS doctor_count
    ORDER BY dept.department_id ASC
    """
    records, _ = db.execute_query(query)
    return {"total": len(records), "items": records}


@router.get("/{department_id}", response_model=DepartmentResponse, summary="Get Department Details")
def get_department(
    department_id: str = Path(..., example="DEP01"),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves details of a specific clinical department."""
    query = """
    MATCH (dept:Department {department_id: $department_id})
    OPTIONAL MATCH (d:Doctor)-[:BELONGS_TO]->(dept)
    RETURN dept.department_id AS department_id,
           dept.name AS name,
           dept.building AS building,
           dept.floor AS floor,
           dept.phone_extension AS phone_extension,
           count(DISTINCT d) AS doctor_count
    """
    records, _ = db.execute_query(query, {"department_id": department_id})
    if not records or not records[0].get("department_id"):
        raise HTTPException(status_code=404, detail=f"Department '{department_id}' not found.")
    return records[0]
