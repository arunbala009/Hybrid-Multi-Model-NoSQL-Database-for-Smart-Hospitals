# Smart Hospital Platform: User Manual & Operator Guide

**Project Title**: Hybrid Multi-Model NoSQL Database for Smart Hospitals  
**System Version**: 1.0.0  
**Target Audience**: Hospital Administrators, Clinicians, Database Evaluators, Academic Examiners  

---

## 1. System Overview

The **Smart Hospital Management & Graph Analytics Platform** is an enterprise-grade clinical prototype integrating native graph databases (Neo4j AuraDB) with embedded semi-structured JSON document models. It provides dual operational capabilities:
1. **Clinical Healthcare Operations**: Patient demographic registration, physician appointments, outpatient/inpatient admissions, and episodic medical charting.
2. **Clinical Decision Intelligence**: Force-directed care pathway visualization, physician caseload analytics, ward bed occupancy monitoring, and simulated epidemiological room-sharing contact tracing.

---

## 2. System Requirements & Prerequisites

- **Operating System**: Windows 10/11, macOS 12+, or Ubuntu 20.04+
- **Python**: Version 3.10 to 3.13
- **Network**: Internet access required if connecting to Neo4j AuraDB cloud instance; offline mock mode supported for local demonstrations.
- **Modern Web Browser**: Google Chrome, Mozilla Firefox, Microsoft Edge, or Safari.

---

## 3. Local Installation & Configuration

### Step 1: Clone or Open Project Workspace
Open a terminal in the root repository directory:
```powershell
cd C:\Users\arunb\.gemini\antigravity-ide\scratch\Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals
```

### Step 2: Initialize Virtual Environment & Install Packages
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### Step 3: Configure Environment Variables
Copy the `.env.example` file to create your local `.env`:
```powershell
Copy-Item .env.example .env
```
Edit `.env` to configure your settings:
```ini
# Neo4j Cloud / Local Credentials
NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-secure-password
NEO4J_DATABASE=neo4j

# API Server Configuration
API_BASE_URL=http://localhost:8000
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
DEBUG=true

# Demo Seeding Authorization Key
DEMO_SEED_TOKEN=hospital-academic-demo-key-2026
```
*(If credentials are kept as placeholders, the application automatically boots into offline mock mode for testing).*

---

## 4. Starting the Application Services

The application operates as two decoupled services: the **FastAPI Backend** and the **Streamlit Frontend**.

### 1. Launch the Backend Server
In Terminal 1:
```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Landing Page: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Launch the Streamlit Frontend Dashboard
In Terminal 2:
```powershell
streamlit run frontend/app.py --server.port 8501
```
The browser will automatically navigate to: [http://localhost:8501](http://localhost:8501).

---

## 5. Dashboard Navigation & Core Workflows

The dashboard provides a persistent sidebar displaying the backend connection status pill (`🟢 Backend Online` or `🔴 Backend Offline`), database mode, navigation menu, and academic metadata.

### View 1: Operational Overview (`Overview`)
- **Executive Metric Cards**: Real-time totals for registered patients, medical staff, clinical departments, total encounters, active inpatient admissions, and total rooms.
- **Caseload Distribution**: Plotly bar chart displaying the count of clinical encounters handled per physician, color-coded by medical specialty.
- **Department Case Volumes**: Interactive donut chart detailing patient case proportions across hospital divisions.
- **Inpatient Room Utilization**: Real-time table displaying ward bed capacity, current occupants, and availability status.

### View 2: Patient Directory & Clinical History (`Patients`)
- **Tab 1 — Directory Search**: Search patients by first name, last name, or ID. Use the pagination selector (10, 25, 50 rows per page) to browse the directory.
- **Tab 2 — Patient Profile & Care History**:
  - Enter a Patient ID (e.g., `P1001`) to inspect the longitudinal medical timeline.
  - Expand "Edit Patient Demographics" to update contact details, emergency contacts, or blood groups.
  - Review historical clinical encounters, attending physicians, admission rooms, and embedded vital signs observations.
  - **Safe Deletion**: To delete an unlinked patient, check the safety confirmation box and click "Delete Patient Record". If the patient has existing clinical history or active admissions, the system blocks deletion and displays an explanatory notice.
- **Tab 3 — Register New Patient**: Enter first name, last name, date of birth (YYYY-MM-DD), gender, blood group, contact phone, and emergency contact. Form validation ensures required fields are filled before submitting to the backend.

### View 3: Medical Staff & Departments (`Doctors & Departments`)
- **Tab 1 — Physician Directory**: Filter physicians by medical specialty (e.g., Cardiology, Neurology) or clinical department. Select a physician to update their contact details, email, or years of experience.
- **Tab 2 — Department Overview**: Displays department divisions, building locations, floor levels, and allocated physician counts.
- **Tab 3 — Workload Analytics**: Compare total encounters handled versus active inpatient cases per physician.
- **Tab 4 — Onboard Physician**: Register a new credentialed doctor, specify their license number, specialty, and associate them directly with a hospital department in Neo4j.

### View 4: Clinical Encounters & Medical Charting (`Encounters & Charting`)
- **Tab 1 — Encounters Registry**: Multi-attribute filtering by encounter status (`Active`, `Discharged`, `Completed`, `Transferred`), encounter type (`Inpatient`, `Outpatient`, `Emergency`), or Patient ID.
- **Tab 2 — Clinical Chart & Discharge**:
  - Enter an Encounter ID (e.g., `ENC1001` or `ENC5001`).
  - View attending physician, assigned ward room, and ICD-10 diagnoses.
  - Inspect the embedded **Document-Style JSON Clinical Record**:
    - **Vital Signs**: Body temperature (°C), heart rate (bpm), blood pressure (mmHg), respiratory rate, and oxygen saturation (SpO2).
    - **Clinical Notes**: Chief complaint, assessment and plan, and discharge summary.
    - **Diagnostic Labs**: Test panels, measured values, units, reference ranges, and abnormal flags (`NORMAL`, `HIGH`, `CRITICAL`).
  - **Discharge Workflow**: Expand "Update Encounter Status / Discharge Patient", select "Discharged", record the discharge summary notes, and commit the update.
- **Tab 3 — Log New Encounter**: Admit a patient by specifying Patient ID, Doctor ID, Encounter Type, Reason for Visit, Room ID (for Inpatients), and initial vital signs measurements.

### View 5: Rooms & Bed Allocation (`Rooms & Bed Allocation`)
- **Inpatient Ward Overview**: Summary cards showing total bed capacity, active inpatients, available beds, and overall hospital occupancy rate (%).
- **Filter Inventory**: Filter rooms by Care Category (`ICU`, `General Ward`, `Private`, `Isolation`) or Floor level.
- **Room History & Co-Occupancy Inspector**: Select any inpatient room to inspect all overlapping patient stays and co-occupancy durations.

### View 6: Graph Relationship Explorer (`Graph Relationship Explorer`)
- **Mode 1 — Patient Care Pathways**:
  - Traces the longitudinal graph path: `Patient -> Encounter -> Doctor -> Department -> Room -> Diagnosis`.
  - Enter an optional Patient ID to isolate a single patient's clinical trajectory, or explore the global hospital graph.
  - Hover over nodes to inspect entity details, specialty, and visit timestamps.
- **Mode 2 — Simulated Room-Sharing & Contact Tracing**:
  - Renders the bipartite contact network connecting patients who occupied the same room during overlapping time intervals.
  - Accompanied by the mandatory epidemiological disclaimer explaining that temporal proximity indicates potential exposure proximity, not clinical transmission.

### View 7: Hospital Analytics (`Hospital Analytics`)
- Dedicated analytical views for clinical administrators:
  - **Physician Caseloads**: Lifetime visits vs current inpatients.
  - **Department Operations**: Encounter volume vs staffing ratios.
  - **Bed Capacity & Occupancy**: Visual comparison of bed capacity versus active inpatients.
  - **Treatment Trajectories**: Inpatient vs outpatient volume breakdowns and top diagnostic condition distributions.

### View 8: Demo Dataset & Seeding Controller (`Demo Dataset & Seeding`)
- **Synthetic Catalog Preview**: Review the specifications for the 20 fictional patients, 8 doctors, 4 departments, 15 rooms, and 35 encounters.
- **Seeding Administration**:
  - **Dry Run Mode (Default)**: Validates dataset integrity and payload schemas offline with **zero database writes**.
  - **Live Seeding Mode**: Requires checking the target approval confirmation and entering the configured `DEMO_SEED_TOKEN` (never displayed in plain text or URLs).

---

## 6. Troubleshooting & Frequently Asked Questions

### 1. "🔴 Backend Offline" indicator appears in the Streamlit sidebar
- **Cause**: The FastAPI backend is not running or is hosted on a different port.
- **Solution**: Open a separate terminal, navigate to the project directory, and start Uvicorn:
  ```powershell
  uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
  ```

### 2. Port Collision (`[Errno 10048] address already in use`)
- **Cause**: Another service is using port 8000 or port 8501.
- **Solution**:
  - For FastAPI, start on port 8001: `uvicorn backend.app.main:app --port 8001`
  - In Streamlit, pass the custom backend URL: set environment variable `$env:BACKEND_URL="http://127.0.0.1:8001"`, then start Streamlit.

### 3. "Cannot delete patient: Patient has existing clinical encounters"
- **Cause**: Referential safety rules prevent deleting patients with care history to protect hospital audit trails.
- **Solution**: This is intended behavior. Deletion is only permitted for newly registered patient identities that have no recorded encounter nodes in the graph.

### 4. Running Automated Tests
- To verify system health without live database connectivity, run:
  ```powershell
  pytest -v
  ```
  All 65 tests should pass in under 2 seconds.
