# Academic Review 2: Working Prototype Specification

**Project Title**: Hybrid Multi-Model NoSQL Database for Smart Hospitals  
**Course Context**: BCSE406 — NoSQL Databases / Advanced Database Systems  
**Repository**: [Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals](https://github.com/arunbala009/Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals.git)  
**Author**: Academic Project Contributor  
**Version**: 1.0.0 (Review Stage 2 Deliverable)  

---

## 1. Prototype Scope & Implemented Capabilities

The working prototype delivers a decoupled, end-to-end clinical operations and graph analytics platform. All operational requirements for patient management, medical staffing, admissions, document-style charting, inpatient room occupancy, and network graph visualization are fully functional.

### Summary of System Scope
- **Backend API**: Asynchronous RESTful service built with FastAPI, providing 17 documented endpoints across 8 resource controllers.
- **Frontend Dashboard**: 8 modular visual views built with Streamlit and Plotly, styled in a modern hospital aesthetic (Navy/Teal/Slate).
- **Data Model**: Hybrid Property Graph (`Patient`, `Doctor`, `Department`, `Encounter`, `Room`, `Diagnosis`, `Medication`) with embedded JSON documents (`ClinicalRecord`).
- **Synthetic Dataset**: Deterministic dataset comprising 20 patients, 8 doctors, 4 departments, 15 inpatient rooms, and 35 clinical encounters.
- **Testing**: 65 automated offline tests across backend schemas, services, API routers, frontend clients, and integration workflows.

---

## 2. Implemented REST API Catalog

The backend runs at `http://127.0.0.1:8000` with interactive OpenAPI documentation available at `/docs`.

| Method | Endpoint Path | Controller | Primary Purpose | Key Parameters / Request Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Root | API landing page & documentation pointers | None |
| `GET` | `/health` | Diagnostics | Liveness probe & database connection state | None |
| `GET` | `/api/v1/health` | Diagnostics | Detailed connectivity diagnostics | None |
| `GET` | `/api/v1/patients` | Patients | Search and paginate patient directory | `skip`, `limit`, `search` |
| `GET` | `/api/v1/patients/{id}` | Patients | Retrieve master demographic profile | `patient_id` |
| `POST` | `/api/v1/patients` | Patients | Register new patient identity | `PatientCreate` (JSON) |
| `PUT` | `/api/v1/patients/{id}` | Patients | Update patient contact/demographics | `PatientUpdate` (JSON) |
| `DELETE` | `/api/v1/patients/{id}` | Patients | Safe deletion (blocked if encounters exist) | `patient_id` |
| `GET` | `/api/v1/patients/{id}/history`| Patients | Longitudinal clinical timeline | `patient_id` |
| `GET` | `/api/v1/doctors` | Doctors | List doctors with specialty/department filters | `skip`, `limit`, `specialty`, `department_id` |
| `GET` | `/api/v1/doctors/{id}` | Doctors | Retrieve physician credentials | `doctor_id` |
| `POST` | `/api/v1/doctors` | Doctors | Onboard credentialed physician | `DoctorCreate` (JSON) |
| `PUT` | `/api/v1/doctors/{id}` | Doctors | Update physician contact/specialty | `DoctorUpdate` (JSON) |
| `DELETE` | `/api/v1/doctors/{id}` | Doctors | Safe deletion (blocked if active cases) | `doctor_id` |
| `GET` | `/api/v1/departments` | Departments | List clinical departments & staff counts | None |
| `GET` | `/api/v1/departments/{id}` | Departments | Get department division details | `department_id` |
| `GET` | `/api/v1/rooms` | Rooms | Inpatient bed inventory and availability | `room_type`, `floor` |
| `GET` | `/api/v1/rooms/{id}` | Rooms | Inspect specific room occupancy | `room_id` |
| `GET` | `/api/v1/encounters` | Encounters | List encounters with status/type filters | `skip`, `limit`, `status`, `encounter_type`, `patient_id` |
| `GET` | `/api/v1/encounters/{id}` | Encounters | Fetch encounter chart with document JSON | `encounter_id` |
| `POST` | `/api/v1/encounters` | Encounters | Log admission with vitals & clinical notes | `EncounterCreate` (JSON) |
| `PUT` | `/api/v1/encounters/{id}` | Encounters | Update encounter status / discharge patient | `EncounterUpdate` (JSON) |
| `GET` | `/api/v1/analytics/overview` | Analytics | Hospital KPIs (patients, doctors, depts, encounters, rooms) | None |
| `GET` | `/api/v1/analytics/doctor-workload` | Analytics | Physician caseload distributions | None |
| `GET` | `/api/v1/analytics/department-statistics` | Analytics | Department patient encounter volumes | None |
| `GET` | `/api/v1/analytics/room-occupancy` | Analytics | Ward bed utilization & active inpatient rates | None |
| `GET` | `/api/v1/analytics/treatment-pathways` | Analytics | Graph care trajectory pathways | `patient_id` (Optional) |
| `GET` | `/api/v1/analytics/room-sharing` | Analytics | Simulated temporal room co-occupancy | `room_id` (Optional) |
| `GET` | `/api/v1/demo/status` | Demo Seeder | Synthetic dataset catalog preview | None |
| `POST` | `/api/v1/demo/seed` | Demo Seeder | Token-authenticated dry-run or live seed | `X-Demo-Token`, `dry_run` |

---

## 3. Streamlit Frontend UI Modules

The frontend runs at `http://localhost:8501` and connects strictly via HTTP to the FastAPI backend:

```text
frontend/
├── app.py                      # Main entry point, theme & view router
├── api_client.py               # Resilient HTTP client managing FastAPI communication
└── components/
    ├── overview_view.py        # Module A: Overview Dashboard
    ├── patients_view.py        # Module B: Patient Directory & Clinical History
    ├── doctors_view.py         # Module C: Medical Staff & Departments
    ├── encounters_view.py      # Module D: Encounters Registry & Medical Charting
    ├── rooms_view.py           # Module E: Hospital Rooms & Bed Allocation
    ├── graph_view.py           # Module F: Graph Relationship Explorer
    ├── analytics_view.py       # Module G: Hospital Analytics Dashboard
    └── demo_view.py            # Module H: Demo Dataset & Seeding Controller
```

### Module Breakdown
- **Module A (Overview)**: 6 high-contrast KPI metric cards, Plotly physician caseload bar chart, department volume pie chart, and live inpatient room occupancy table.
- **Module B (Patients)**: Search-as-you-type input, pagination selector, patient detail profile, longitudinal care timeline with status badges, demographic editing form, and safe deletion modal.
- **Module C (Doctors & Depts)**: Multi-attribute filtering (specialty, department), physician update form, department staffing table, and credential onboarding form.
- **Module D (Encounters)**: Filters for encounter status (`Active`, `Discharged`, `Completed`) and encounter type (`Inpatient`, `Outpatient`, `Emergency`); detailed view displaying embedded semi-structured JSON document (vitals, notes, labs); discharge form with ISO-8601 timestamps.
- **Module E (Rooms)**: Floor and room type filters (`ICU`, `General Ward`, `Private`, `Isolation`); bed capacity calculation; room co-occupancy inspector displaying overlapping admissions.
- **Module F (Graph Explorer)**: Interactive Plotly/NetworkX 2D graph viewer with two visualization modes: (1) Patient Care Pathways (`Patient -> Encounter -> Doctor / Dept / Room / Diag`), (2) Simulated Room-Sharing Contact Tracing with required epidemiological disclaimers.
- **Module G (Analytics)**: Tabbed analytical views covering physician caseloads, department volume distributions, ward bed utilization, and diagnostic frequencies.
- **Module H (Demo Seeder)**: Fictional catalog specification preview and token-authenticated seeder controller with dry-run default (zero database writes).

---

## 4. Automated Testing Evidence

All tests run 100% offline using `pytest` without requiring live Neo4j credentials or network access:

```powershell
pytest -v
```

### Test Suite Execution Output
```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\arunb\.gemini\antigravity-ide\scratch\Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals
configfile: pytest.ini
testpaths: backend/tests, frontend/tests
plugins: anyio-4.15.1
collected 65 items

backend\tests\test_analytics.py ......                                   [  9%]
backend\tests\test_doctors.py ....                                       [ 15%]
backend\tests\test_encounters.py ....                                    [ 21%]
backend\tests\test_health.py ...                                         [ 26%]
backend\tests\test_integration_workflows.py .....                        [ 33%]
backend\tests\test_patients.py ........                                  [ 46%]
backend\tests\test_schema_design.py ...........                          [ 63%]
backend\tests\test_seed.py ....                                          [ 69%]
frontend\tests\test_api_client.py ....................                   [100%]

============================= 65 passed in 1.37s ==============================
```

### Test Distribution by Functional Domain
- **Schema & Constraints (`test_schema_design.py`)**: 11 tests verifying 7 uniqueness constraints, 6 property indexes, idempotent Cypher syntax, and Pydantic JSON roundtrip serialization.
- **Patient Operations (`test_patients.py`)**: 8 tests verifying pagination, ID search, duplicate rejection, Pydantic validation errors, safe deletion rules, and longitudinal history.
- **Physician Operations (`test_doctors.py`)**: 4 tests verifying specialty filtering, department affiliation, and deletion safety checks.
- **Encounter & Document Modeling (`test_encounters.py`)**: 4 tests verifying valid document-style JSON ingestion, physiological vitals range validation, and discharge workflows.
- **Diagnostics & Health (`test_health.py`)**: 3 tests verifying OpenAPI root pointers, connected health state, and degraded offline state.
- **Synthetic Data Seeder (`test_seed.py`)**: 4 tests verifying deterministic dataset counts, catalog endpoints, unauthorized rejection, and authorized dry-run execution.
- **End-to-End Integration Workflows (`test_integration_workflows.py`)**: 5 multi-step integration workflows covering patient lifecycle, doctor affiliation, document charting, room occupancy, and seeder boundary enforcement.
- **Frontend API Client (`test_api_client.py`)**: 20 tests verifying HTTP request formatting, 503 connection error handling, 504 timeouts, 404/409 error parsing, and authentication headers.

---

## 5. Local Setup & Execution Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.13.2)
- PowerShell (Windows) or Bash (macOS/Linux)

### 1. Initialize Virtual Environment & Install Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Configure Environment Template
```powershell
Copy-Item .env.example .env
```
*(Leave placeholder values for offline development and automated testing).*

### 3. Start the Backend API Server
```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Probe: `http://127.0.0.1:8000/health`

### 4. Start the Frontend Dashboard
In a separate terminal window:
```powershell
streamlit run frontend/app.py --server.port 8501
```
- Dashboard Interface: `http://localhost:8501`

---

## 6. Academic Demonstration & Screenshot Checklist

When presenting Review 2 to evaluators, capture and highlight the following key interfaces:

- [ ] **Screenshot 1: FastAPI Swagger Explorer (`/docs`)**
  - Demonstrates interactive OpenAPI interface with 17 endpoints and full Pydantic schema schemas.
- [ ] **Screenshot 2: Overview Dashboard**
  - Highlights hospital KPI metric cards, doctor workload distribution bar chart, and bed occupancy table.
- [ ] **Screenshot 3: Patient Longitudinal History**
  - Demonstrates the patient care timeline with visit badges and embedded vital signs summary.
- [ ] **Screenshot 4: Document-Style Medical Charting**
  - Shows the semi-structured JSON clinical record (vital signs observation, physician assessment & plan, lab test flags).
- [ ] **Screenshot 5: Inpatient Room Bed Utilization**
  - Shows live bed occupancy tracking distinguishing active admissions from historical stays.
- [ ] **Screenshot 6: Interactive Graph Care Pathways**
  - Displays the 2D NetworkX/Plotly network topology connecting `Patient -> Encounter -> Doctor -> Department -> Room -> Diagnosis`.
- [ ] **Screenshot 7: Simulated Room-Sharing Contact Tracing**
  - Demonstrates co-occupancy contact network with the prominent academic/epidemiological disclaimer banner.
- [ ] **Screenshot 8: Automated Test Execution Output**
  - Terminal screenshot proving all 65 automated tests passing cleanly in ~1.3 seconds without live database writes.
