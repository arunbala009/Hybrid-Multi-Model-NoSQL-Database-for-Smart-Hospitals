"""
Patients API Router
===================
RESTful endpoints for Patient registration, profile updates, directory searches,
safe deletion, and complete longitudinal clinical history retrieval.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from backend.app.database import DatabaseManager, get_db
from backend.app.models.patient import (
    PatientCreate, PatientUpdate, PatientResponse, PatientListResponse
)
from backend.app.services.patient_service import PatientService

router = APIRouter(prefix="/api/v1/patients", tags=["Patients"])


def get_patient_service(db: DatabaseManager = Depends(get_db)) -> PatientService:
    return PatientService(db)


@router.get("", response_model=PatientListResponse, summary="List Patients")
def list_patients(
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    search: Optional[str] = Query(None, description="Search by name or patient ID"),
    service: PatientService = Depends(get_patient_service)
):
    """Retrieves paginated list of patients with optional full-text search."""
    return service.list_patients(skip=skip, limit=limit, search=search)


@router.get("/{patient_id}", response_model=PatientResponse, summary="Get Patient Details")
def get_patient(
    patient_id: str = Path(..., description="Unique patient identifier", example="P1001"),
    service: PatientService = Depends(get_patient_service)
):
    """Retrieves demographic details of a single patient."""
    return service.get_patient(patient_id)


@router.post("", response_model=PatientResponse, status_code=201, summary="Register New Patient")
def create_patient(
    payload: PatientCreate,
    service: PatientService = Depends(get_patient_service)
):
    """Registers a new patient with unique ID."""
    return service.create_patient(payload)


@router.put("/{patient_id}", response_model=PatientResponse, summary="Update Patient Demographics")
def update_patient(
    patient_id: str = Path(..., example="P1001"),
    payload: PatientUpdate = ...,
    service: PatientService = Depends(get_patient_service)
):
    """Updates demographic attributes of an existing patient."""
    return service.update_patient(patient_id, payload)


@router.delete("/{patient_id}", summary="Delete Patient Record")
def delete_patient(
    patient_id: str = Path(..., example="P1001"),
    service: PatientService = Depends(get_patient_service)
):
    """
    Safely removes a patient node. Rejects deletion if active or historical encounters
    exist to preserve clinical audit trails.
    """
    return service.delete_patient(patient_id)


@router.get("/{patient_id}/history", summary="Get Longitudinal Clinical History")
def get_patient_history(
    patient_id: str = Path(..., example="P1001"),
    service: PatientService = Depends(get_patient_service)
):
    """
    Traverses graph relationships to return a patient's complete clinical timeline,
    attending physicians, diagnoses, medications, and embedded clinical notes.
    """
    return service.get_patient_history(patient_id)
