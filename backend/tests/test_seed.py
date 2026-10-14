"""
Synthetic Seeding and Demo Authentication Tests
================================================
Verifies deterministic dataset structure (20 patients, 8 doctors, 4 depts, 15 rooms, 35 encounters)
and enforces token-based authorization on the demo seeding endpoint.
"""

from fastapi.testclient import TestClient
from backend.app.config import settings
from backend.app.services.seed_service import (
    SeedService, PATIENTS_DATA, DOCTORS_DATA, DEPARTMENTS_DATA, ROOMS_DATA, ENCOUNTERS_DATA
)


def test_seed_dataset_exact_counts():
    """Verifies the exact target volumes requested for academic demonstration."""
    assert len(PATIENTS_DATA) == 20, f"Expected 20 patients, found {len(PATIENTS_DATA)}"
    assert len(DOCTORS_DATA) == 8, f"Expected 8 doctors, found {len(DOCTORS_DATA)}"
    assert len(DEPARTMENTS_DATA) == 4, f"Expected 4 departments, found {len(DEPARTMENTS_DATA)}"
    assert len(ROOMS_DATA) == 15, f"Expected 15 rooms, found {len(ROOMS_DATA)}"
    assert len(ENCOUNTERS_DATA) == 35, f"Expected 35 encounters, found {len(ENCOUNTERS_DATA)}"


def test_demo_status_endpoint(client: TestClient):
    """Verifies offline dataset catalog preview."""
    res = client.get("/api/v1/demo/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    catalog = data["dataset_specification"]
    assert catalog["patients"] == 20
    assert catalog["doctors"] == 8
    assert catalog["departments"] == 4
    assert catalog["rooms"] == 15
    assert catalog["encounters"] == 35


def test_seed_endpoint_unauthorized_rejection(client: TestClient):
    """Verifies 401 Unauthorized when no demo token or an invalid token is provided."""
    # Missing token
    res1 = client.post("/api/v1/demo/seed")
    assert res1.status_code == 401

    # Invalid token
    res2 = client.post("/api/v1/demo/seed", headers={"X-Demo-Token": "wrong-token"})
    assert res2.status_code == 401


def test_seed_endpoint_authorized_dry_run(client: TestClient):
    """Verifies authorized request with dry_run=true returns success without executing live database writes."""
    headers = {"X-Demo-Token": settings.DEMO_SEED_TOKEN}
    res = client.post("/api/v1/demo/seed?dry_run=true", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "dry_run_success"
    assert data["patients"] == 20
    assert data["encounters"] == 35
