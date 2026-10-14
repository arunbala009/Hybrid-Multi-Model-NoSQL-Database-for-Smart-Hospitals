"""
Clinical and Operational Graph Analytics Router
================================================
Endpoints exposing multi-hop Cypher analytics: hospital KPIs, doctor caseloads,
real-time room occupancy, longitudinal care pathways, and epidemiological contact tracing.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from backend.app.database import DatabaseManager, get_db
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["Hospital Graph Analytics"])


def get_analytics_service(db: DatabaseManager = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/overview", summary="Hospital Aggregate KPIs")
def get_overview(service: AnalyticsService = Depends(get_analytics_service)):
    """Computes total counts of patients, doctors, departments, active encounters, and rooms."""
    return service.get_overview_analytics()


@router.get("/doctor-workload", summary="Physician Caseload Analysis")
def get_doctor_workload(service: AnalyticsService = Depends(get_analytics_service)):
    """Returns patient encounter volumes and active cases distributed across medical staff."""
    return service.get_doctor_workload()


@router.get("/department-statistics", summary="Department Operational Metrics")
def get_department_statistics(service: AnalyticsService = Depends(get_analytics_service)):
    """Returns department encounter volumes, physician counts, and active cases."""
    return service.get_department_statistics()


@router.get("/room-occupancy", summary="Real-Time Ward & Bed Utilization")
def get_room_occupancy(service: AnalyticsService = Depends(get_analytics_service)):
    """
    Computes current room occupancy based on Active inpatient admissions.
    Discharged patients are strictly excluded from current occupancy calculations.
    """
    return service.get_room_occupancy()


@router.get("/treatment-pathways", summary="Longitudinal Patient Treatment Pathways")
def get_treatment_pathways(
    patient_id: Optional[str] = Query(None, description="Optional patient filter", example="P1001"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Traces multi-hop patient care journeys, ordered chronologically across admissions,
    attending specialists, department transfers, diagnoses, and drug regimens.
    """
    return service.get_treatment_pathways(patient_id=patient_id)


@router.get("/room-sharing", summary="Cross-Infection Room Sharing & Contact Tracing")
def get_room_sharing(
    room_id: Optional[str] = Query(None, description="Filter by room ID", example="RM-GEN-201"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Simulated Epidemiological Contact Analysis:
    Identifies pairs of patients whose room stays overlapped in time within shared wards.
    Excludes non-overlapping historical room usages to avoid false positive contact links.
    """
    return service.get_room_sharing_analysis(room_id=room_id)
