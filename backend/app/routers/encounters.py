"""
Encounters API Router
=====================
RESTful endpoints for clinical admissions, outpatient visits, and medical record documentation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from backend.app.database import DatabaseManager, get_db
from backend.app.models.encounter import (
    EncounterCreate, EncounterUpdate, EncounterResponse, EncounterListResponse
)
from backend.app.services.encounter_service import EncounterService

router = APIRouter(prefix="/api/v1/encounters", tags=["Encounters & Admissions"])


def get_encounter_service(db: DatabaseManager = Depends(get_db)) -> EncounterService:
    return EncounterService(db)


@router.get("", response_model=EncounterListResponse, summary="List Encounters")
def list_encounters(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Active, Discharged, Completed"),
    encounter_type: Optional[str] = Query(None, description="Inpatient, Outpatient, Emergency"),
    patient_id: Optional[str] = Query(None, description="Filter by Patient ID"),
    service: EncounterService = Depends(get_encounter_service)
):
    """Retrieves paginated clinical encounters with filtering by status, type, and patient."""
    return service.list_encounters(
        skip=skip, limit=limit, status=status, encounter_type=encounter_type, patient_id=patient_id
    )


@router.get("/{encounter_id}", response_model=EncounterResponse, summary="Get Encounter Details")
def get_encounter(
    encounter_id: str = Path(..., example="ENC7001"),
    service: EncounterService = Depends(get_encounter_service)
):
    """Retrieves details of an encounter, including parsed clinical record JSON and attending physician."""
    return service.get_encounter(encounter_id)


@router.post("", response_model=EncounterResponse, status_code=201, summary="Log New Clinical Encounter")
def create_encounter(
    payload: EncounterCreate,
    service: EncounterService = Depends(get_encounter_service)
):
    """Logs an inpatient admission, outpatient consultation, or emergency triage visit."""
    return service.create_encounter(payload)


@router.put("/{encounter_id}", response_model=EncounterResponse, summary="Update Encounter or Discharge")
def update_encounter(
    encounter_id: str = Path(..., example="ENC7001"),
    payload: EncounterUpdate = ...,
    service: EncounterService = Depends(get_encounter_service)
):
    """Updates encounter status, records discharge timestamp, or updates clinical chart notes."""
    return service.update_encounter(encounter_id, payload)
