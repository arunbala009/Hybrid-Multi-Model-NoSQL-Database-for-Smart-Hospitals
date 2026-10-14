# Backend API: Smart Hospital Management & Graph Analytics

FastAPI asynchronous RESTful backend service for the **Hybrid Multi-Model NoSQL Database for Smart Hospitals** platform. It connects to **Neo4j AuraDB** using the official Python driver and implements parameterized Cypher queries alongside embedded JSON clinical charting.

---

## 🏛️ Modular Architecture

```text
backend/
├── app/
│   ├── config.py             # Environment settings & credential masking
│   ├── database.py           # Neo4j driver lifecycle & parameterized query executor
│   ├── main.py               # FastAPI application initialization & middleware
│   ├── models/               # Pydantic schemas for data validation
│   │   ├── patient.py        # Patient demographic models
│   │   ├── doctor.py         # Physician profiles & specialty filters
│   │   ├── department.py     # Division details & doctor count aggregations
│   │   ├── room.py           # Room capacity & live bed availability
│   │   └── encounter.py      # Encounters & embedded ClinicalRecord JSON document
│   ├── routers/              # RESTful API route controllers (/api/v1)
│   │   ├── health.py         # Container liveness probes & DB ping
│   │   ├── patients.py       # Patient CRUD & clinical history
│   │   ├── doctors.py        # Physician CRUD & department assignments
│   │   ├── departments.py    # Department directory & staffing
│   │   ├── rooms.py          # Bed management & room allocations
│   │   ├── encounters.py     # Inpatient admissions & outpatient visits
│   │   ├── analytics.py      # Multi-hop graph analytics & contact tracing
│   │   └── demo.py           # Secure synthetic data seeding
│   └── services/             # Core business logic & Cypher execution
│       ├── patient_service.py
│       ├── doctor_service.py
│       ├── encounter_service.py
│       ├── analytics_service.py
│       └── seed_service.py   # Deterministic synthetic hospital generator
├── tests/                    # Automated offline pytest suite (MockDatabase)
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_patients.py
│   ├── test_doctors.py
│   ├── test_encounters.py
│   ├── test_analytics.py
│   ├── test_seed.py
│   └── test_schema_design.py
└── requirements.txt
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the project root:
```ini
NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-secure-password
NEO4J_DATABASE=neo4j

API_BASE_URL=http://localhost:8000
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
DEBUG=true
DEMO_SEED_TOKEN=hospital-academic-demo-key-2026
```

---

## 🚀 Local Execution (PowerShell)

### 1. Set Up Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 2. Run Automated Test Suite
All 40 unit and API tests execute offline with **zero live database writes**:
```powershell
pytest backend/tests -v
```

### 3. Start Development Server
```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive OpenAPI Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
ReDoc Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔒 Security & Safe Deletion Enforcement

1. **Credential Masking**: `config.py` overrides `__repr__` to prevent sensitive credentials from ever appearing in logs, traces, or debug outputs.
2. **Safe Deletion Protocol**: Patient and Doctor records cannot be deleted if active or historical encounters are linked in the graph (`409 Conflict`), preserving clinical audit trails.
3. **Demo Token Protection**: The `/api/v1/demo/seed` endpoint requires the `X-Demo-Token` header, validated using constant-time comparison (`secrets.compare_digest`).
