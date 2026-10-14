"""
Health and System Route Tests
==============================
Verifies startup, root index documentation, and health check routes.
"""

from fastapi.testclient import TestClient
from backend.tests.conftest import MockDatabaseManager


def test_root_index_endpoint(client: TestClient):
    """Verifies service landing index and OpenAPI documentation pointers."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert "endpoints" in data
    assert data["endpoints"]["health"] == "/health"
    assert data["endpoints"]["patients"] == "/api/v1/patients"


def test_health_endpoint_connected(client: TestClient, mock_db: MockDatabaseManager):
    """Verifies /health when database connectivity check succeeds."""
    mock_db.set_connected(True)
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True


def test_health_endpoint_degraded(client: TestClient, mock_db: MockDatabaseManager):
    """Verifies /api/v1/health indicates degraded status without crashing when DB is offline."""
    mock_db.set_connected(False)
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "degraded"
    assert data["database"]["connected"] is False
