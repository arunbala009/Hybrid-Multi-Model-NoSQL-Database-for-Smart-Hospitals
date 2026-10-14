"""
Smart Hospital Management & Analytics API Entry Point
======================================================
FastAPI application initialization, router aggregation, CORS middleware,
and graceful driver lifecycle management.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import db
from backend.app.routers import (
    health_router,
    patients_router,
    doctors_router,
    departments_router,
    rooms_router,
    encounters_router,
    analytics_router,
    demo_router
)

# Configure application logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("smart_hospital.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Manager:
    Connects to Neo4j on startup if live credentials are configured.
    Ensures safe, graceful driver connection cleanup on shutdown.
    """
    logger.info("Starting Smart Hospital API (Environment: %s)...", settings.ENVIRONMENT)
    try:
        driver = db.connect()
        if driver:
            logger.info("Neo4j database connection established.")
        else:
            logger.info("Operating without active Neo4j connection (offline/mock mode).")
    except Exception as exc:
        logger.warning("Database connection deferred or operating offline: %s", str(exc))

    yield

    logger.info("Shutting down Smart Hospital API...")
    db.close()


app = FastAPI(
    title="Hybrid Multi-Model NoSQL Database for Smart Hospitals API",
    description=(
        "Academic Capstone Project (BCSE406 NoSQL Databases): "
        "A decoupled healthcare management and graph analytics platform leveraging "
        "Neo4j AuraDB (Index-Free Adjacency) and embedded JSON clinical document records."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(patients_router)
app.include_router(doctors_router)
app.include_router(departments_router)
app.include_router(rooms_router)
app.include_router(encounters_router)
app.include_router(analytics_router)
app.include_router(demo_router)


@app.get("/", tags=["Root"])
def root_index():
    """Service landing endpoint with API index and documentation links."""
    return {
        "service": "Hybrid Multi-Model NoSQL Database for Smart Hospitals",
        "academic_project": "BCSE406 NoSQL Databases",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "openapi_specification": "/openapi.json",
        "endpoints": {
            "health": "/health",
            "api_health": "/api/v1/health",
            "patients": "/api/v1/patients",
            "doctors": "/api/v1/doctors",
            "departments": "/api/v1/departments",
            "rooms": "/api/v1/rooms",
            "encounters": "/api/v1/encounters",
            "analytics_overview": "/api/v1/analytics/overview",
            "analytics_doctor_workload": "/api/v1/analytics/doctor-workload",
            "analytics_department_stats": "/api/v1/analytics/department-statistics",
            "analytics_room_occupancy": "/api/v1/analytics/room-occupancy",
            "analytics_treatment_pathways": "/api/v1/analytics/treatment-pathways",
            "analytics_room_sharing": "/api/v1/analytics/room-sharing",
            "demo_status": "/api/v1/demo/status",
            "demo_seed": "/api/v1/demo/seed"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
