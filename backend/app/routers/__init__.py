"""
API Routers Package
"""

from backend.app.routers.health import router as health_router
from backend.app.routers.patients import router as patients_router
from backend.app.routers.doctors import router as doctors_router
from backend.app.routers.departments import router as departments_router
from backend.app.routers.rooms import router as rooms_router
from backend.app.routers.encounters import router as encounters_router
from backend.app.routers.analytics import router as analytics_router
from backend.app.routers.demo import router as demo_router

__all__ = [
    "health_router",
    "patients_router",
    "doctors_router",
    "departments_router",
    "rooms_router",
    "encounters_router",
    "analytics_router",
    "demo_router"
]
