# Smart Hospital Operations Dashboard (Streamlit Frontend)

> **Phase 4 Deliverable**  
> A modern, responsive clinical operations and graph analytics dashboard built with **Streamlit** and **Plotly**, connecting to the FastAPI backend via robust HTTP RESTful APIs.

---

## 🏗️ Architecture & Component Design

The frontend is organized into a modular, maintainable structure where UI components, business views, and networking logic are strictly decoupled:

```text
frontend/
├── app.py                      # Main Streamlit application entry point & view router
├── api_client.py               # Centralized HTTP API client with timeouts & error trapping
├── requirements.txt            # Frontend dependencies (streamlit, plotly, networkx, pyvis, requests)
├── components/                 # Specialized UI views & analytical modules
│   ├── __init__.py
│   ├── overview_view.py        # Executive hospital KPIs, live occupancy & caseload distribution
│   ├── patients_view.py        # Patient directory, longitudinal care timeline, registration & deletion
│   ├── doctors_view.py         # Physician directory, department affiliation, caseload analytics
│   ├── encounters_view.py      # Encounters registry, document vitals/notes, discharge workflows
│   ├── rooms_view.py           # Bed allocation, room types, active vs historical stays
│   ├── graph_view.py           # Interactive Plotly/NetworkX graph explorer (pathways & contacts)
│   ├── analytics_view.py       # Comprehensive cross-entity clinical and operational intelligence
│   └── demo_view.py            # Synthetic dataset catalog & token-authenticated seeder controller
└── tests/
    ├── __init__.py
    └── test_api_client.py      # 20 unit tests with mocked backend responses (0 live DB writes)
```

---

## 🎨 Visual Design System

The dashboard implements a modern Hospital Information System (HIS) aesthetic defined in `.streamlit/config.toml`:
- **Primary Color**: `#0D9488` (Teal)
- **Background Color**: `#0F172A` (Deep Navy)
- **Secondary Background Color**: `#1E293B` (Dark Slate)
- **Text Color**: `#F8FAFC` (Off-White)
- **KPI Metrics**: Large high-contrast cards with subtle badges and clean typography (`sans serif`).
- **Charts & Graphs**: Responsive Plotly figures with dark-mode transparent backgrounds.
- **Micro-states**: Comprehensive loading spinners (`st.spinner`), empty state helpers, and clear validation notices.

---

## 🔌 API Client (`api_client.py`)

- **Decoupled Architecture**: All networking is mediated through `HospitalAPIClient`. Streamlit never communicates directly with Neo4j.
- **Dynamic Configuration**: Automatically reads `BACKEND_URL` or `API_BASE_URL` from Streamlit secrets, environment variables, or defaults to `http://localhost:8000`.
- **Fault Tolerance**:
  - Connection timeouts: 5s connect, 20s read.
  - Connection errors return user-friendly messages (`503 Backend Offline`).
  - Timeout errors return clean warnings (`504 Gateway Timeout`).
  - HTTP 4xx/5xx responses parsed safely with JSON detail fallbacks.
- **Zero Secret Exposure**: Passwords and administrative tokens are never logged or stored in client code.

---

## 📋 Implemented Dashboard Views

| View Name | Core Capabilities | API Endpoints Utilized |
| :--- | :--- | :--- |
| **Overview** | Hospital KPIs (patients, doctors, depts, encounters, admissions, rooms), caseload charts, bed utilization table | `/api/v1/analytics/overview`, `/api/v1/analytics/doctor-workload`, `/api/v1/analytics/department-statistics`, `/api/v1/analytics/room-occupancy` |
| **Patients** | Search, pagination, longitudinal care timeline, demographic editor, validated patient registration, safe deletion rules | `/api/v1/patients`, `/api/v1/patients/{id}`, `/api/v1/patients/{id}/history` |
| **Doctors & Depts** | Filter by specialty/department, physician profile editor, staffing analysis, credential onboarding form | `/api/v1/doctors`, `/api/v1/departments`, `/api/v1/analytics/doctor-workload` |
| **Encounters & Charting** | Filter by status/type/patient, inspect semi-structured JSON document (vitals, notes, labs), discharge patient form | `/api/v1/encounters`, `/api/v1/encounters/{id}` |
| **Rooms & Beds** | Bed capacity, filter by acuity/floor, active inpatient vs historical stay co-occupancy inspector | `/api/v1/rooms`, `/api/v1/analytics/room-occupancy`, `/api/v1/analytics/room-sharing` |
| **Graph Explorer** | Interactive 2D NetworkX/Plotly topology: (1) Patient Care Pathways, (2) Simulated Room-Sharing Contact Tracing | `/api/v1/analytics/treatment-pathways`, `/api/v1/analytics/room-sharing` |
| **Hospital Analytics** | Doctor caseload distribution, department volume breakdown, bed utilization metrics, clinical diagnostic trajectories | `/api/v1/analytics/*` |
| **Demo Data & Seeding** | Catalog overview (20 patients, 8 doctors, 4 depts, 15 rooms, 35 encounters), token-authenticated seeder controller with dry-run default | `/api/v1/demo/status`, `/api/v1/demo/seed` |

> [!WARNING]
> **Epidemiological Modeling Disclaimer**: The contact analysis visualization identifies temporal room overlap between patients sharing inpatient spaces. It is strictly illustrative and academic, not clinical proof of pathogen transmission.

---

## 🚀 Local Startup Instructions

### 1. Start the FastAPI Backend
In a terminal window:
```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 2. Launch the Streamlit Frontend
In a second terminal window:
```powershell
streamlit run frontend/app.py --server.port 8501
```
The browser will automatically open to `http://localhost:8501`.

---

## 🧪 Testing

The frontend test suite (`frontend/tests/test_api_client.py`) executes 20 offline unit tests with mocked backend responses:
```powershell
pytest frontend/tests -v
```
All tests run 100% offline with zero live database dependencies or network writes.
