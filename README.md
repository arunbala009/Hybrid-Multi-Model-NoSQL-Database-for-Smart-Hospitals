# Hybrid Multi-Model NoSQL Database for Smart Hospitals

> **Academic Capstone Project**  
> An intelligent clinical operations and healthcare management platform powered by a hybrid multi-model NoSQL architecture, combining native graph relationships (Neo4j AuraDB) with flexible document-oriented clinical records.

---

## 🏥 Problem Statement & Motivation

Modern hospital management systems face significant challenges with relational databases (RDBMS) when modeling highly interconnected clinical and operational workflows:
1. **Multi-Hop Traversal Bottlenecks**: Tracing patient referral trails, infection contact chains, cross-consultation networks, and multi-department transfers requires complex recursive joins and Common Table Expressions (CTEs), leading to exponential $O(N^k)$ performance degradation.
2. **Rigid Clinical Schemas**: Diagnostic procedures, episodic encounter notes, lab test metrics, and dynamic medication regimens vary wildly across medical specialties, resulting in sparse, unwieldy tables with hundreds of nullable columns in traditional SQL schemas.
3. **Siloed Analytical & Operational Views**: Clinical administrators need both graph-level topological insights (e.g., doctor workload networks, disease contact tracing, bed allocation bottlenecks) and rich document-style clinical encounter histories.

### The Solution: Hybrid Multi-Model NoSQL Architecture
This project implements a hybrid multi-model NoSQL platform:
- **Graph Model (Neo4j & Cypher)**: Models healthcare entities (`Patient`, `Doctor`, `Department`, `Encounter`, `Diagnosis`, `Medication`, `Room`) and their explicit relationships (`HAS_ENCOUNTER`, `ATTENDED_BY`, `BELONGS_TO`, `DIAGNOSED_WITH`, `PRESCRIBED`, `ADMITTED_TO`, `HAS_ALLERGY_TO`, `HEAD_OF`) with native index-free adjacency.
- **Document Model (Embedded JSON Payloads)**: Stores episodic clinical histories, vital signs, lab values, and diagnostic logs as structured JSON objects within encounter entities, enabling schema-agnostic medical charting.

> [!IMPORTANT]
> **Academic Prototype & Privacy Disclaimer**: All patient data, doctor profiles, medical encounters, and test results utilized or generated in this system are strictly synthetic and fictional. This prototype is designed exclusively for academic demonstration and research purposes and is not intended for real clinical deployment.

---

## 🎯 Project Objectives

- **Demonstrate NoSQL Concepts**: Contrast graph traversals and document storage against traditional relational paradigms.
- **Implement Robust Graph Relationships**: Capture end-to-end patient care pathways, department hierarchies, and resource allocations.
- **Provide Clinical Decision Analytics**: Deliver graph algorithms for patient journey tracking, cross-infection contact tracing, and departmental patient-flow bottleneck detection.
- **Deliver Full-Stack Production Readiness**: Build a decoupled RESTful backend with FastAPI and a modern interactive clinical dashboard using Streamlit.
- **Support Academic Evaluation**: Satisfy all academic assessment criteria across Reviews 1, 2, and 3 with full documentation and benchmark evaluations.

---

## 🛠️ Technology Stack & Implementation Status

| Layer | Technology | Role & Purpose | Status |
| :--- | :--- | :--- | :--- |
| **Database** | **Neo4j AuraDB (Free Tier)** | Cloud-managed native graph database with Cypher query engine | Integrated & Verified |
| **Backend API** | **FastAPI (Python 3.12+)** | Asynchronous, high-performance RESTful API with Pydantic validation | ✅ **Implemented (Phase 3)** |
| **ASGI Server** | **Uvicorn** | Production-ready ASGI web server | ✅ **Implemented (Phase 3)** |
| **Document Model**| **Pydantic / Embedded JSON** | Semi-structured clinical record documentation on encounters | ✅ **Implemented (Phase 3)** |
| **Frontend UI** | **Streamlit** | Interactive medical intelligence dashboard with dynamic visualization | ✅ **Implemented (Phase 4)** |
| **Graph Visuals** | **Plotly / NetworkX** | Interactive 2D graph explorer for care pathways and contacts | ✅ **Implemented (Phase 4)** |
| **Testing** | **Pytest / HTTPX / Mocks** | Automated offline API, schema, query, & UI client test suite (60 tests) | ✅ **100% Passing (Phase 4)** |
| **Hosting (API)** | **Render** | Cloud containerized web service | `[PLANNED: Phase 6]` |
| **Hosting (UI)** | **Streamlit Cloud** | Publicly accessible community cloud deployment | `[PLANNED: Phase 6]` |

---

## 📁 Project Structure

```text
Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals/
├── backend/
│   ├── README.md             # Backend architecture & developer documentation
│   ├── requirements.txt      # FastAPI, Neo4j, Pydantic, pytest dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py         # Environment settings & credential protection
│   │   ├── database.py       # Neo4j driver lifecycle & parameterized query manager
│   │   ├── main.py           # FastAPI entry point, CORS, and route aggregation
│   │   ├── models/           # Pydantic schemas (Patient, Doctor, Room, Encounter, Vitals)
│   │   ├── routers/          # RESTful controllers (/health, /patients, /analytics, etc.)
│   │   └── services/         # Business logic & Cypher graph analytical queries
│   └── tests/                # 40 automated offline backend tests (0 live DB writes)
├── frontend/
│   ├── README.md             # Frontend architecture & component documentation
│   ├── requirements.txt      # Streamlit, Plotly, NetworkX, Requests dependencies
│   ├── app.py                # Streamlit entry point, theme & view router
│   ├── api_client.py         # Resilient HTTP client managing FastAPI communication
│   ├── components/           # Modular view components (Overview, Patients, Rooms, etc.)
│   └── tests/                # 20 automated offline frontend client tests
├── docs/
│   ├── IMPLEMENTATION_PLAN.md# Six-phase project roadmap
│   ├── DATABASE_DESIGN.md    # Complete graph schema, Mermaid diagrams & queries
│   └── API_DOCUMENTATION.md  # Complete RESTful endpoint catalog & payload examples
├── scripts/
│   └── init_schema.py        # Idempotent Cypher constraints and indexes script
├── .streamlit/
│   └── config.toml           # Hospital dashboard theme (Navy/Teal/Slate)
├── pytest.ini                # Pytest configuration (--import-mode=importlib)
├── .env.example              # Safe environment variable template with placeholders
├── .gitignore                # Comprehensive exclusion list for secrets and caches
├── requirements.txt          # Root dependency pointers
└── README.md                 # Project documentation
```

---

## 💻 Local Setup & Execution Guide (PowerShell)

### 1. Set Up Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Neo4j AuraDB credentials:
```powershell
Copy-Item .env.example .env
```
*(Never commit `.env` or share real passwords.)*

### 3. Run Automated Tests
Execute the full comprehensive offline test suite (65 tests, 0 database writes):
```powershell
pytest -v
```

### 4. Start the FastAPI Backend Server
In your first terminal:
```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger API Explorer: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc API Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- System Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 5. Start the Streamlit Frontend Dashboard
In a second terminal:
```powershell
streamlit run frontend/app.py --server.port 8501
```
The application will launch at: [http://localhost:8501](http://localhost:8501)

---

## 📜 Academic Review & Examination Deliverables

The project provides complete academic deliverables under [`docs/reviews/`](docs/reviews/):

- **Review 1 — Design & Architecture**: Problem statement, literature review, multi-model rationale, schema architecture, and RDBMS vs NoSQL comparison ([`docs/reviews/REVIEW_1_DESIGN_AND_ARCHITECTURE.md`](docs/reviews/REVIEW_1_DESIGN_AND_ARCHITECTURE.md)).
- **Review 2 — Working Prototype**: Complete REST API catalog, Streamlit UI modules, automated testing evidence, and student demonstration checklist ([`docs/reviews/REVIEW_2_WORKING_PROTOTYPE.md`](docs/reviews/REVIEW_2_WORKING_PROTOTYPE.md)).
- **Review 3 — Final Evaluation**: Traversal complexity analysis ($O(1)$ vs $O(N^k)$), query expressiveness, limitations, deployment readiness, and future research directions ([`docs/reviews/REVIEW_3_FINAL_EVALUATION.md`](docs/reviews/REVIEW_3_FINAL_EVALUATION.md)).
- **User Manual**: End-to-end setup, service execution, navigation across all 8 views, CRUD workflows, and troubleshooting guide ([`docs/reviews/USER_MANUAL.md`](docs/reviews/USER_MANUAL.md)).
- **Viva Voce Question Bank**: 30 project-specific questions and technical answers covering Neo4j, Cypher, NoSQL theory, FastAPI, security, and testing ([`docs/reviews/VIVA_QUESTIONS.md`](docs/reviews/VIVA_QUESTIONS.md)).
- **Evaluation Plan**: Reproducible experimental benchmark protocols for traversal latency, document sizing, API throughput, and concurrency ([`docs/reviews/EVALUATION_PLAN.md`](docs/reviews/EVALUATION_PLAN.md)).
