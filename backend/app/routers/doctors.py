"""
Doctors API Router
==================
RESTful endpoints for Physician directory, specialty filtering, and credentials management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from backend.app.database import DatabaseManager, get_db
from backend.app.models.doctor import (
    DoctorCreate, DoctorUpdate, DoctorResponse, DoctorListResponse
)
from backend.app.services.doctor_service import DoctorService

router = APIRouter(prefix="/api/v1/doctors", tags=["Doctors & Specialists"])


def get_doctor_service(db: DatabaseManager = Depends(get_db)) -> DoctorService:
    return DoctorService(db)


@router.get("", response_model=DoctorListResponse, summary="List Physicians")
def list_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    specialty: Optional[str] = Query(None, description="Filter by specialty (e.g., Cardiology)"),
    department_id: Optional[str] = Query(None, description="Filter by Department ID (e.g., DEP01)"),
    service: DoctorService = Depends(get_doctor_service)
):
    """Retrieves paginated doctor directory with optional specialty and department filters."""
    return service.list_doctors(skip=skip, limit=limit, specialty=specialty, department_id=department_id)


@router.get("/{doctor_id}", response_model=DoctorResponse, summary="Get Doctor Profile")
def get_doctor(
    doctor_id: str = Path(..., example="DOC101"),
    service: DoctorService = Depends(get_doctor_service)
):
    """Retrieves single doctor profile and department affiliation."""
    return service.get_doctor(doctor_id)


@router.post("", response_model=DoctorResponse, status_code=201, summary="Register Physician")
def create_doctor(
    payload: DoctorCreate,
    service: DoctorService = Depends(get_doctor_service)
):
    """Creates a new physician record and affiliates them with a department."""
    return service.create_doctor(payload)


@router.put("/{doctor_id}", response_model=DoctorResponse, summary="Update Doctor Profile")
def update_doctor(
    doctor_id: str = Path(..., example="DOC101"),
    payload: DoctorUpdate = ...,
    service: DoctorService = Depends(get_doctor_service)
):
    """Updates doctor details and re-assigns department if requested."""
    return service.update_doctor(doctor_id, payload)


@router.delete("/{doctor_id}", summary="Delete Physician")
def delete_doctor(
    doctor_id: str = Path(..., example="DOC101"),
    service: DoctorService = Depends(get_doctor_service)
):
    """Safely removes a physician. Rejects deletion if active clinical cases exist."""
    return service.delete_doctor(doctor_id)
