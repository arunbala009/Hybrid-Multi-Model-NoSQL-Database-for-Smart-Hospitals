"""
Hospital Backend API Client
===========================
Centralized HTTP client managing communication with the FastAPI backend.
Handles connection timeouts, response parsing, and graceful error handling.
"""

import os
import requests
from typing import Dict, Any, Optional

try:
    import streamlit as st
except ImportError:
    st = None


class HospitalAPIClient:
    """Encapsulates all RESTful communication with the Smart Hospital FastAPI backend."""

    def __init__(self, base_url: Optional[str] = None):
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            # Check Streamlit secrets, then environment variable, then default localhost
            url = None
            if st is not None:
                try:
                    url = st.secrets.get("BACKEND_URL") or st.secrets.get("API_BASE_URL")
                except Exception:
                    url = None

            if not url:
                url = os.getenv("BACKEND_URL") or os.getenv("API_BASE_URL") or "http://localhost:8000"

            self.base_url = url.rstrip("/")

        self.timeout = (5.0, 20.0)  # (connect timeout, read timeout)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Core request handler with error trapping."""
        url = f"{self.base_url}{path}"
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=req_headers,
                timeout=self.timeout
            )

            # Try parsing JSON response
            try:
                body = response.json()
            except Exception:
                body = {"text": response.text}

            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "data": body,
                    "error": None,
                    "status_code": response.status_code
                }

            # Handle 4xx / 5xx responses
            detail = body.get("detail", str(body)) if isinstance(body, dict) else str(body)
            return {
                "success": False,
                "data": None,
                "error": detail,
                "status_code": response.status_code
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "data": None,
                "error": f"Cannot connect to backend API at {self.base_url}. Ensure FastAPI is running.",
                "status_code": 503
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "data": None,
                "error": "Request timed out while waiting for backend response.",
                "status_code": 504
            }
        except Exception as exc:
            return {
                "success": False,
                "data": None,
                "error": f"Unexpected client error: {str(exc)}",
                "status_code": 500
            }

    # --------------------------------------------------------------------------
    # Health Diagnostics
    # --------------------------------------------------------------------------
    def check_health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    # --------------------------------------------------------------------------
    # Patients
    # --------------------------------------------------------------------------
    def get_patients(self, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> Dict[str, Any]:
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        return self._request("GET", "/api/v1/patients", params=params)

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/patients/{patient_id}")

    def create_patient(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/patients", json_data=payload)

    def update_patient(self, patient_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/v1/patients/{patient_id}", json_data=payload)

    def delete_patient(self, patient_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/v1/patients/{patient_id}")

    def get_patient_history(self, patient_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/patients/{patient_id}/history")

    # --------------------------------------------------------------------------
    # Doctors & Departments
    # --------------------------------------------------------------------------
    def get_doctors(
        self,
        skip: int = 0,
        limit: int = 50,
        specialty: Optional[str] = None,
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"skip": skip, "limit": limit}
        if specialty:
            params["specialty"] = specialty
        if department_id:
            params["department_id"] = department_id
        return self._request("GET", "/api/v1/doctors", params=params)

    def get_doctor(self, doctor_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/doctors/{doctor_id}")

    def create_doctor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/doctors", json_data=payload)

    def update_doctor(self, doctor_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/v1/doctors/{doctor_id}", json_data=payload)

    def delete_doctor(self, doctor_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/v1/doctors/{doctor_id}")

    def get_departments(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/departments")

    def get_department(self, department_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/departments/{department_id}")

    # --------------------------------------------------------------------------
    # Rooms & Beds
    # --------------------------------------------------------------------------
    def get_rooms(self, room_type: Optional[str] = None, floor: Optional[int] = None) -> Dict[str, Any]:
        params = {}
        if room_type:
            params["room_type"] = room_type
        if floor is not None:
            params["floor"] = floor
        return self._request("GET", "/api/v1/rooms", params=params)

    def get_room(self, room_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/rooms/{room_id}")

    # --------------------------------------------------------------------------
    # Encounters & Clinical History
    # --------------------------------------------------------------------------
    def get_encounters(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        encounter_type: Optional[str] = None,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if encounter_type:
            params["encounter_type"] = encounter_type
        if patient_id:
            params["patient_id"] = patient_id
        return self._request("GET", "/api/v1/encounters", params=params)

    def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/encounters/{encounter_id}")

    def create_encounter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/encounters", json_data=payload)

    def update_encounter(self, encounter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/v1/encounters/{encounter_id}", json_data=payload)

    # --------------------------------------------------------------------------
    # Graph Analytics
    # --------------------------------------------------------------------------
    def get_overview_analytics(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/analytics/overview")

    def get_doctor_workload(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/analytics/doctor-workload")

    def get_department_statistics(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/analytics/department-statistics")

    def get_room_occupancy(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/analytics/room-occupancy")

    def get_treatment_pathways(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        params = {"patient_id": patient_id} if patient_id else None
        return self._request("GET", "/api/v1/analytics/treatment-pathways", params=params)

    def get_room_sharing(self, room_id: Optional[str] = None) -> Dict[str, Any]:
        params = {"room_id": room_id} if room_id else None
        return self._request("GET", "/api/v1/analytics/room-sharing", params=params)

    # --------------------------------------------------------------------------
    # Demo Seeding Controls
    # --------------------------------------------------------------------------
    def get_demo_status(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/demo/status")

    def seed_demo_data(self, token: str, dry_run: bool = True) -> Dict[str, Any]:
        headers = {"X-Demo-Token": token}
        params = {"dry_run": "true" if dry_run else "false"}
        return self._request("POST", "/api/v1/demo/seed", headers=headers, params=params)
