# RESTful API Specification: Smart Hospital Management & Analytics

> **Base Route**: `/api/v1`  
> **Interactive Swagger UI**: `/docs`  
> **Authentication**: All operational endpoints are open; `/api/v1/demo/seed` requires header `X-Demo-Token`.

---

## 📑 Endpoint Catalog Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness probe returning system and Neo4j connectivity status |
| `GET` | `/api/v1/health` | Detailed health diagnostics |
| `GET` | `/api/v1/patients` | Paginated patient directory with name search (`skip`, `limit`, `search`) |
| `GET` | `/api/v1/patients/{patient_id}` | Fetch demographic profile of a single patient |
| `POST` | `/api/v1/patients` | Register a new patient node |
| `PUT` | `/api/v1/patients/{patient_id}` | Update patient demographic attributes |
| `DELETE`| `/api/v1/patients/{patient_id}`| Safe delete (blocks with 409 if active clinical history exists) |
| `GET` | `/api/v1/patients/{patient_id}/history` | Longitudinal clinical care history, diagnoses, and prescriptions |
| `GET` | `/api/v1/doctors` | Paginated physician directory (filter by `specialty` or `department_id`) |
| `GET` | `/api/v1/doctors/{doctor_id}` | Fetch physician profile and department affiliation |
| `POST` | `/api/v1/doctors` | Register physician and create `[:BELONGS_TO]` relationship |
| `PUT` | `/api/v1/doctors/{doctor_id}` | Update physician attributes and department |
| `DELETE`| `/api/v1/doctors/{doctor_id}` | Safe delete (blocks with 409 if assigned encounters exist) |
| `GET` | `/api/v1/departments` | List clinical divisions and physician headcounts |
| `GET` | `/api/v1/departments/{department_id}` | Fetch single department details |
| `GET` | `/api/v1/rooms` | List inpatient rooms, calculating real-time occupancy and availability |
| `GET` | `/api/v1/rooms/{room_id}` | Fetch single room capacity and current occupants |
| `GET` | `/api/v1/encounters` | List clinical encounters (filter by `status`, `encounter_type`, `patient_id`) |
| `GET` | `/api/v1/encounters/{encounter_id}` | Fetch encounter with parsed embedded JSON clinical document |
| `POST` | `/api/v1/encounters` | Log new inpatient admission, outpatient visit, or emergency triage |
| `PUT` | `/api/v1/encounters/{encounter_id}`| Update encounter status, record discharge, or update chart notes |
| `GET` | `/api/v1/analytics/overview` | Hospital aggregate KPIs (patients, doctors, admissions, rooms) |
| `GET` | `/api/v1/analytics/doctor-workload` | Physician caseload comparison and active patient counts |
| `GET` | `/api/v1/analytics/department-statistics` | Departmental admission volumes and staffing levels |
| `GET` | `/api/v1/analytics/room-occupancy` | Current bed utilization (strictly excludes discharged stays) |
| `GET` | `/api/v1/analytics/treatment-pathways` | Chronological multi-hop patient care journeys |
| `GET` | `/api/v1/analytics/room-sharing` | Simulated cross-infection room overlap contact tracing |
| `GET` | `/api/v1/demo/status` | Offline synthetic dataset catalog preview |
| `POST` | `/api/v1/demo/seed` | Trigger deterministic synthetic data seeder (Requires `X-Demo-Token`) |

---

## 🧪 Request & Response Examples

### 1. Patient Registration (`POST /api/v1/patients`)
**Request Body**:
```json
{
  "first_name": "Eleanor",
  "last_name": "Vane",
  "dob": "1991-03-22",
  "gender": "Female",
  "blood_group": "B+",
  "contact_phone": "+1-555-4422",
  "emergency_contact": "Charles Vane (+1-555-4423)"
}
```
**Response (`201 Created`)**:
```json
{
  "patient_id": "P5F3A10C",
  "first_name": "Eleanor",
  "last_name": "Vane",
  "dob": "1991-03-22",
  "gender": "Female",
  "blood_group": "B+",
  "contact_phone": "+1-555-4422",
  "emergency_contact": "Charles Vane (+1-555-4423)",
  "created_at": "2026-10-15T00:20:00Z"
}
```

---

### 2. Clinical Encounter Logging with Document Model (`POST /api/v1/encounters`)
**Request Body**:
```json
{
  "patient_id": "P1001",
  "doctor_id": "DOC101",
  "room_id": "RM-ICU-301",
  "encounter_type": "Inpatient",
  "status": "Active",
  "start_time": "2026-10-15T08:30:00Z",
  "reason_for_visit": "Acute severe shortness of breath and fever",
  "clinical_record": {
    "vital_signs": {
      "temperature_celsius": 38.4,
      "heart_rate_bpm": 104,
      "blood_pressure": {
        "systolic_mmhg": 138,
        "diastolic_mmhg": 88
      },
      "respiratory_rate_bpm": 22,
      "oxygen_saturation_percent": 94,
      "recorded_at": "2026-10-15T08:35:00Z"
    },
    "clinical_notes": {
      "chief_complaint": "Acute productive cough, dyspnea, and fever for 4 days.",
      "assessment_and_plan": "Community-acquired right lower lobe pneumonia. Initiating intravenous Ceftriaxone."
    }
  }
}
```
**Response (`201 Created`)**:
```json
{
  "encounter_id": "ENC9B210",
  "patient_id": "P1001",
  "patient_name": "Arthur Pendleton",
  "doctor_id": "DOC101",
  "doctor_name": "Arun Sharma",
  "department_name": "Cardiology",
  "room_number": "ICU-301",
  "encounter_type": "Inpatient",
  "status": "Active",
  "start_time": "2026-10-15T08:30:00Z",
  "end_time": null,
  "reason_for_visit": "Acute severe shortness of breath and fever",
  "diagnoses": [],
  "prescriptions": [],
  "clinical_record": {
    "vital_signs": {
      "temperature_celsius": 38.4,
      "heart_rate_bpm": 104,
      "blood_pressure": {
        "systolic_mmhg": 138,
        "diastolic_mmhg": 88
      },
      "respiratory_rate_bpm": 22,
      "oxygen_saturation_percent": 94
    },
    "clinical_notes": {
      "chief_complaint": "Acute productive cough, dyspnea, and fever for 4 days.",
      "assessment_and_plan": "Community-acquired right lower lobe pneumonia. Initiating intravenous Ceftriaxone."
    }
  }
}
```

---

### 3. Cross-Infection Room Sharing Contact Tracing (`GET /api/v1/analytics/room-sharing`)
**Response (`200 OK`)**:
```json
{
  "disclaimer": "Simulated contact-analysis demonstration. Temporal room overlap indicates potential epidemiological exposure proximity; not clinical proof of transmission.",
  "contact_pairs_count": 2,
  "query_time_ms": 2,
  "overlapping_encounters": [
    {
      "room_id": "RM-GEN-201",
      "room_number": "GW-201",
      "room_type": "General Ward",
      "patient_1_id": "P1001",
      "patient_1_name": "Arthur Pendleton",
      "encounter_1_id": "ENC7001",
      "patient_1_admit": "2026-10-01T08:00:00Z",
      "patient_1_discharge": "2026-10-05T14:00:00Z",
      "patient_2_id": "P1002",
      "patient_2_name": "Beatrice Holloway",
      "encounter_2_id": "ENC7002",
      "patient_2_admit": "2026-10-03T10:00:00Z",
      "patient_2_discharge": "2026-10-07T12:00:00Z"
    }
  ]
}
```

---

### 4. Synthetic Seeder Trigger (`POST /api/v1/demo/seed`)
**Headers**:
`X-Demo-Token: hospital-academic-demo-key-2026`

**Query**:
`?dry_run=true`

**Response (`200 OK`)**:
```json
{
  "status": "dry_run_success",
  "message": "Synthetic dataset validated offline. Zero database writes performed.",
  "departments": 4,
  "doctors": 8,
  "rooms": 15,
  "patients": 20,
  "diagnoses": 8,
  "medications": 8,
  "encounters": 35
}
```
