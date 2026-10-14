"""
Health and System Diagnostics Router
====================================
Endpoints for container liveness/readiness probes and Neo4j connectivity status.
"""

from fastapi import APIRouter, Depends
from backend.app.config import settings
from backend.app.database import DatabaseManager, get_db

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", summary="Basic Liveness Probe")
@router.get("/api/v1/health", summary="Detailed Health Check")
def get_health_status(db: DatabaseManager = Depends(get_db)):
    """
    Returns system status and verifies whether the Neo4j driver has active connectivity.
    Never exposes passwords, tokens, or raw host secrets.
    """
    is_configured = settings.is_neo4j_configured()
    is_connected = db.is_connected()
    connection_state = "connected" if is_connected else ("unconfigured" if not is_configured else "connection_failed")

    return {
        "status": "healthy" if is_connected else "degraded",
        "service": "Smart Hospital Management API",
        "version": "1.0.0",
        "database": {
            "connected": is_connected,
            "configured": is_configured,
            "state": connection_state,
            "engine": "Neo4j AuraDB / Property Graph",
            "mode": "live" if is_connected else ("unconfigured" if not is_configured else "offline_or_mock")
        }
    }
