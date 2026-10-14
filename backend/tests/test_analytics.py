"""
Graph Analytics Route Tests
===========================
Verifies hospital KPIs, physician workloads, department stats, live room occupancy,
longitudinal care pathways, and epidemiological contact tracing.
"""

from fastapi.testclient import TestClient


def test_analytics_overview(client: TestClient):
    """Verifies aggregate hospital KPI metrics endpoint."""
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_patients" in data
    assert "total_doctors" in data
    assert "total_departments" in data
    assert "total_encounters" in data
    assert "active_admissions" in data


def test_analytics_doctor_workload(client: TestClient):
    """Verifies doctor caseload distribution endpoint."""
    res = client.get("/api/v1/analytics/doctor-workload")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total_doctors_evaluated" in data


def test_analytics_department_statistics(client: TestClient):
    """Verifies department-level case volumes and staffing statistics."""
    res = client.get("/api/v1/analytics/department-statistics")
    assert res.status_code == 200
    data = res.json()
    assert "departments" in data


def test_analytics_room_occupancy(client: TestClient):
    """Verifies live room occupancy calculation."""
    res = client.get("/api/v1/analytics/room-occupancy")
    assert res.status_code == 200
    data = res.json()
    assert "total_rooms" in data
    assert "occupied_rooms" in data
    assert "occupancy_rate_percent" in data


def test_analytics_treatment_pathways(client: TestClient):
    """Verifies sequential care pathway traversal."""
    res = client.get("/api/v1/analytics/treatment-pathways?patient_id=P1001")
    assert res.status_code == 200
    data = res.json()
    assert "pathways" in data


def test_analytics_room_sharing_contact_tracing(client: TestClient):
    """Verifies simulated cross-infection room-sharing contact analysis."""
    res = client.get("/api/v1/analytics/room-sharing?room_id=RM-GEN-201")
    assert res.status_code == 200
    data = res.json()
    assert "disclaimer" in data
    assert "Simulated contact-analysis" in data["disclaimer"]
    assert "overlapping_encounters" in data
