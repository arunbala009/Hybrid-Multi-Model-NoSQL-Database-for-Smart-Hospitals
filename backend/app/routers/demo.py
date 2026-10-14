"""
Synthetic Demo Data Seeding Router
===================================
Endpoints for previewing and securely triggering the deterministic synthetic data seeder.
Requires a secure authentication token to prevent unauthorized modification.
"""

import secrets
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, HTTPException, status
from backend.app.config import settings
from backend.app.database import DatabaseManager, get_db
from backend.app.services.seed_service import SeedService

router = APIRouter(prefix="/api/v1/demo", tags=["Synthetic Demo & Seeding"])


def verify_demo_token(
    x_demo_token: Optional[str] = Header(None, alias="X-Demo-Token"),
    token: Optional[str] = Query(None, description="Alternative query token")
) -> bool:
    """Safely verifies the demo administration token using constant-time string comparison."""
    provided_token = x_demo_token or token
    if not provided_token or not secrets.compare_digest(provided_token, settings.DEMO_SEED_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing demo administration token."
        )
    return True


@router.get("/status", summary="Synthetic Dataset Catalog Preview")
def get_demo_status():
    """Returns a preview of the deterministic synthetic hospital dataset offline."""
    return {
        "status": "ready",
        "dataset_specification": SeedService.get_synthetic_dataset_preview()
    }


@router.post("/seed", summary="Seed Synthetic Hospital Dataset")
def seed_hospital_data(
    dry_run: bool = Query(True, description="When true, performs validation only without database writes"),
    authorized: bool = Depends(verify_demo_token),
    db: DatabaseManager = Depends(get_db)
):
    """
    Seeds 20 fictional patients, 8 doctors, 4 departments, 15 rooms, and 35 encounters.
    Protected by demo token authorization. Default is dry_run=True to prevent accidental writes.
    """
    service = SeedService(db)
    return service.seed_database(dry_run=dry_run)
