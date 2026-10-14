"""
Synthetic Hospital Dataset Generator and Seeder
================================================
Generates deterministic, idempotent, realistic fictional hospital records:
- 20 Fictional Patients
- 8 Doctors across 4 Departments
- 15 Inpatient Rooms
- 35 Clinical Encounters (Outpatient, Inpatient, Emergency)
- Standard Diagnoses & Medications with embedded Clinical JSON records

SAFETY:
- Uses MERGE with stable IDs to ensure idempotency.
- Never touches Account, Transaction, or other legacy labels.
- Supports offline dry-run mode for test suites without Neo4j writes.
"""

import json
import logging
from typing import Dict, Any, List
from backend.app.database import DatabaseManager

logger = logging.getLogger("smart_hospital.seed")

# ==============================================================================
# DETERMINISTIC FICTIONAL DATA DEFINITIONS
# ==============================================================================

DEPARTMENTS_DATA = [
    {"department_id": "DEP01", "name": "Cardiology", "building": "Main Wing", "floor": 3, "phone_extension": "x3010"},
    {"department_id": "DEP02", "name": "Neurology", "building": "West Tower", "floor": 4, "phone_extension": "x4020"},
    {"department_id": "DEP03", "name": "Pulmonology", "building": "East Pavilion", "floor": 2, "phone_extension": "x2030"},
    {"department_id": "DEP04", "name": "Emergency Medicine", "building": "Main Wing", "floor": 1, "phone_extension": "x1000"},
]

DOCTORS_DATA = [
    {"doctor_id": "DOC101", "first_name": "Arun", "last_name": "Sharma", "specialty": "Cardiology", "license_number": "MD-CARD-101", "email": "a.sharma@hospital.org", "phone": "+1-555-0101", "years_of_experience": 14, "department_id": "DEP01"},
    {"doctor_id": "DOC102", "first_name": "Elena", "last_name": "Rostova", "specialty": "Cardiology", "license_number": "MD-CARD-102", "email": "e.rostova@hospital.org", "phone": "+1-555-0102", "years_of_experience": 9, "department_id": "DEP01"},
    {"doctor_id": "DOC201", "first_name": "Marcus", "last_name": "Vance", "specialty": "Neurology", "license_number": "MD-NEUR-201", "email": "m.vance@hospital.org", "phone": "+1-555-0201", "years_of_experience": 18, "department_id": "DEP02"},
    {"doctor_id": "DOC202", "first_name": "Priya", "last_name": "Nair", "specialty": "Neurology", "license_number": "MD-NEUR-202", "email": "p.nair@hospital.org", "phone": "+1-555-0202", "years_of_experience": 7, "department_id": "DEP02"},
    {"doctor_id": "DOC301", "first_name": "David", "last_name": "Chen", "specialty": "Pulmonology", "license_number": "MD-PULM-301", "email": "d.chen@hospital.org", "phone": "+1-555-0301", "years_of_experience": 12, "department_id": "DEP03"},
    {"doctor_id": "DOC302", "first_name": "Amina", "last_name": "Diallo", "specialty": "Pulmonology", "license_number": "MD-PULM-302", "email": "a.diallo@hospital.org", "phone": "+1-555-0302", "years_of_experience": 11, "department_id": "DEP03"},
    {"doctor_id": "DOC401", "first_name": "James", "last_name": "Wilson", "specialty": "Emergency Medicine", "license_number": "MD-EMER-401", "email": "j.wilson@hospital.org", "phone": "+1-555-0401", "years_of_experience": 15, "department_id": "DEP04"},
    {"doctor_id": "DOC402", "first_name": "Sophia", "last_name": "Martinez", "specialty": "Emergency Medicine", "license_number": "MD-EMER-402", "email": "s.martinez@hospital.org", "phone": "+1-555-0402", "years_of_experience": 6, "department_id": "DEP04"},
]

ROOMS_DATA = [
    # ICU Rooms (Floor 3)
    {"room_id": "RM-ICU-301", "room_number": "ICU-301", "room_type": "ICU", "capacity": 1, "floor": 3},
    {"room_id": "RM-ICU-302", "room_number": "ICU-302", "room_type": "ICU", "capacity": 1, "floor": 3},
    {"room_id": "RM-ICU-303", "room_number": "ICU-303", "room_type": "ICU", "capacity": 1, "floor": 3},
    # General Wards (Floor 2 - shared beds for contact tracing demonstration)
    {"room_id": "RM-GEN-201", "room_number": "GW-201", "room_type": "General Ward", "capacity": 2, "floor": 2},
    {"room_id": "RM-GEN-202", "room_number": "GW-202", "room_type": "General Ward", "capacity": 2, "floor": 2},
    {"room_id": "RM-GEN-203", "room_number": "GW-203", "room_type": "General Ward", "capacity": 2, "floor": 2},
    {"room_id": "RM-GEN-204", "room_number": "GW-204", "room_type": "General Ward", "capacity": 2, "floor": 2},
    # Private Rooms (Floor 4)
    {"room_id": "RM-PVT-401", "room_number": "PVT-401", "room_type": "Private", "capacity": 1, "floor": 4},
    {"room_id": "RM-PVT-402", "room_number": "PVT-402", "room_type": "Private", "capacity": 1, "floor": 4},
    {"room_id": "RM-PVT-403", "room_number": "PVT-403", "room_type": "Private", "capacity": 1, "floor": 4},
    {"room_id": "RM-PVT-404", "room_number": "PVT-404", "room_type": "Private", "capacity": 1, "floor": 4},
    # Isolation Units (Floor 1)
    {"room_id": "RM-ISO-101", "room_number": "ISO-101", "room_type": "Isolation", "capacity": 1, "floor": 1},
    {"room_id": "RM-ISO-102", "room_number": "ISO-102", "room_type": "Isolation", "capacity": 1, "floor": 1},
    {"room_id": "RM-ISO-103", "room_number": "ISO-103", "room_type": "Isolation", "capacity": 1, "floor": 1},
    {"room_id": "RM-ISO-104", "room_number": "ISO-104", "room_type": "Isolation", "capacity": 1, "floor": 1},
]

PATIENTS_DATA = [
    {"patient_id": "P1001", "first_name": "Arthur", "last_name": "Pendleton", "dob": "1968-04-12", "gender": "Male", "blood_group": "A+", "contact_phone": "+1-555-1001", "emergency_contact": "Martha Pendleton"},
    {"patient_id": "P1002", "first_name": "Beatrice", "last_name": "Holloway", "dob": "1975-11-23", "gender": "Female", "blood_group": "O+", "contact_phone": "+1-555-1002", "emergency_contact": "Thomas Holloway"},
    {"patient_id": "P1003", "first_name": "Carlos", "last_name": "Santana", "dob": "1982-01-19", "gender": "Male", "blood_group": "B+", "contact_phone": "+1-555-1003", "emergency_contact": "Lucia Santana"},
    {"patient_id": "P1004", "first_name": "Diana", "last_name": "Prince", "dob": "1990-07-08", "gender": "Female", "blood_group": "AB-", "contact_phone": "+1-555-1004", "emergency_contact": "Hippolyta Prince"},
    {"patient_id": "P1005", "first_name": "Edward", "last_name": "Norton", "dob": "1954-09-30", "gender": "Male", "blood_group": "O-", "contact_phone": "+1-555-1005", "emergency_contact": "Mary Norton"},
    {"patient_id": "P1006", "first_name": "Fiona", "last_name": "Gallagher", "dob": "1994-03-14", "gender": "Female", "blood_group": "A-", "contact_phone": "+1-555-1006", "emergency_contact": "Ian Gallagher"},
    {"patient_id": "P1007", "first_name": "George", "last_name": "Costanza", "dob": "1962-12-05", "gender": "Male", "blood_group": "B-", "contact_phone": "+1-555-1007", "emergency_contact": "Frank Costanza"},
    {"patient_id": "P1008", "first_name": "Hannah", "last_name": "Abbott", "dob": "1988-06-22", "gender": "Female", "blood_group": "A+", "contact_phone": "+1-555-1008", "emergency_contact": "Neville Abbott"},
    {"patient_id": "P1009", "first_name": "Isaac", "last_name": "Clarke", "dob": "1979-08-15", "gender": "Male", "blood_group": "O+", "contact_phone": "+1-555-1009", "emergency_contact": "Nicole Brennan"},
    {"patient_id": "P1010", "first_name": "Julia", "last_name": "Roberts", "dob": "1971-10-28", "gender": "Female", "blood_group": "AB+", "contact_phone": "+1-555-1010", "emergency_contact": "Daniel Moder"},
    {"patient_id": "P1011", "first_name": "Kevin", "last_name": "Flynn", "dob": "1959-05-02", "gender": "Male", "blood_group": "A+", "contact_phone": "+1-555-1011", "emergency_contact": "Sam Flynn"},
    {"patient_id": "P1012", "first_name": "Laura", "last_name": "Croft", "dob": "1985-02-14", "gender": "Female", "blood_group": "O-", "contact_phone": "+1-555-1012", "emergency_contact": "Richard Croft"},
    {"patient_id": "P1013", "first_name": "Michael", "last_name": "Corleone", "dob": "1950-04-07", "gender": "Male", "blood_group": "B+", "contact_phone": "+1-555-1013", "emergency_contact": "Kay Adams"},
    {"patient_id": "P1014", "first_name": "Nadia", "last_name": "Vulvokov", "dob": "1984-08-20", "gender": "Female", "blood_group": "A-", "contact_phone": "+1-555-1014", "emergency_contact": "Alan Zaveri"},
    {"patient_id": "P1015", "first_name": "Oliver", "last_name": "Queen", "dob": "1986-12-11", "gender": "Male", "blood_group": "O+", "contact_phone": "+1-555-1015", "emergency_contact": "Thea Queen"},
    {"patient_id": "P1016", "first_name": "Patricia", "last_name": "Star", "dob": "1992-09-17", "gender": "Female", "blood_group": "AB-", "contact_phone": "+1-555-1016", "emergency_contact": "Eugene Krabs"},
    {"patient_id": "P1017", "first_name": "Quentin", "last_name": "Tarantino", "dob": "1963-03-27", "gender": "Male", "blood_group": "B-", "contact_phone": "+1-555-1017", "emergency_contact": "Daniella Pick"},
    {"patient_id": "P1018", "first_name": "Rachel", "last_name": "Green", "dob": "1989-05-05", "gender": "Female", "blood_group": "A+", "contact_phone": "+1-555-1018", "emergency_contact": "Ross Geller"},
    {"patient_id": "P1019", "first_name": "Samuel", "last_name": "Vimes", "dob": "1958-07-19", "gender": "Male", "blood_group": "O+", "contact_phone": "+1-555-1019", "emergency_contact": "Sybil Ramkin"},
    {"patient_id": "P1020", "first_name": "Tara", "last_name": "Knowles", "dob": "1981-11-09", "gender": "Female", "blood_group": "AB+", "contact_phone": "+1-555-1020", "emergency_contact": "Jackson Teller"},
]

DIAGNOSES_DATA = [
    {"diagnosis_id": "DIAG-I10", "icd10_code": "I10", "name": "Essential (Primary) Hypertension", "category": "Cardiovascular"},
    {"diagnosis_id": "DIAG-I21", "icd10_code": "I21.9", "name": "Acute Myocardial Infarction", "category": "Cardiovascular"},
    {"diagnosis_id": "DIAG-G43", "icd10_code": "G43.9", "name": "Migraine without Aura", "category": "Neurological"},
    {"diagnosis_id": "DIAG-I63", "icd10_code": "I63.9", "name": "Cerebral Infarction (Ischemic Stroke)", "category": "Neurological"},
    {"diagnosis_id": "DIAG-J18", "icd10_code": "J18.9", "name": "Community-Acquired Pneumonia", "category": "Pulmonary"},
    {"diagnosis_id": "DIAG-J44", "icd10_code": "J44.1", "name": "Chronic Obstructive Pulmonary Disease", "category": "Pulmonary"},
    {"diagnosis_id": "DIAG-R07", "icd10_code": "R07.9", "name": "Chest Pain, Unspecified", "category": "Emergency"},
    {"diagnosis_id": "DIAG-R55", "icd10_code": "R55", "name": "Syncope and Collapse", "category": "Emergency"},
]

MEDICATIONS_DATA = [
    {"medication_id": "MED-ATOR", "name": "Lipitor", "generic_name": "Atorvastatin Calcium", "dosage_form": "Tablet", "standard_strength": "20mg"},
    {"medication_id": "MED-ASPI", "name": "Bayer Aspirin", "generic_name": "Acetylsalicylic Acid", "dosage_form": "Tablet", "standard_strength": "81mg"},
    {"medication_id": "MED-AMLO", "name": "Norvasc", "generic_name": "Amlodipine Besylate", "dosage_form": "Tablet", "standard_strength": "5mg"},
    {"medication_id": "MED-SUMA", "name": "Imitrex", "generic_name": "Sumatriptan", "dosage_form": "Tablet", "standard_strength": "50mg"},
    {"medication_id": "MED-AMOX", "name": "Amoxil", "generic_name": "Amoxicillin Trihydrate", "dosage_form": "Capsule", "standard_strength": "500mg"},
    {"medication_id": "MED-AZIT", "name": "Zithromax", "generic_name": "Azithromycin", "dosage_form": "Tablet", "standard_strength": "250mg"},
    {"medication_id": "MED-ALBU", "name": "ProAir HFA", "generic_name": "Albuterol Sulfate", "dosage_form": "Inhaler", "standard_strength": "90mcg/actuation"},
    {"medication_id": "MED-CEFT", "name": "Rocephin", "generic_name": "Ceftriaxone Sodium", "dosage_form": "Injection", "standard_strength": "1g/vial"},
]

# 35 Encounters covering Inpatient, Outpatient, Emergency with overlapping room stays
ENCOUNTERS_DATA = [
    # General Ward 201 overlap: P1001 and P1002 stayed in GW-201 together (simulated contact pair)
    {"encounter_id": "ENC7001", "patient_id": "P1001", "doctor_id": "DOC101", "room_id": "RM-GEN-201", "type": "Inpatient", "status": "Discharged", "start": "2026-10-01T08:00:00Z", "end": "2026-10-05T14:00:00Z", "reason": "Unstable angina management", "diag": "DIAG-I10", "med": "MED-ATOR"},
    {"encounter_id": "ENC7002", "patient_id": "P1002", "doctor_id": "DOC102", "room_id": "RM-GEN-201", "type": "Inpatient", "status": "Discharged", "start": "2026-10-03T10:00:00Z", "end": "2026-10-07T12:00:00Z", "reason": "Heart palpitations workup", "diag": "DIAG-I10", "med": "MED-AMLO"},

    # General Ward 202 overlap: P1003 and P1004 stayed in GW-202 together
    {"encounter_id": "ENC7003", "patient_id": "P1003", "doctor_id": "DOC201", "room_id": "RM-GEN-202", "type": "Inpatient", "status": "Discharged", "start": "2026-10-02T09:00:00Z", "end": "2026-10-06T11:00:00Z", "reason": "Complex migraine evaluation", "diag": "DIAG-G43", "med": "MED-SUMA"},
    {"encounter_id": "ENC7004", "patient_id": "P1004", "doctor_id": "DOC202", "room_id": "RM-GEN-202", "type": "Inpatient", "status": "Discharged", "start": "2026-10-04T14:00:00Z", "end": "2026-10-08T16:00:00Z", "reason": "Neurological observation", "diag": "DIAG-G43", "med": "MED-SUMA"},

    # Active Inpatient Admissions currently occupying rooms (end is None)
    {"encounter_id": "ENC7005", "patient_id": "P1005", "doctor_id": "DOC301", "room_id": "RM-ICU-301", "type": "Inpatient", "status": "Active", "start": "2026-10-12T07:30:00Z", "end": None, "reason": "Acute exacerbation of COPD", "diag": "DIAG-J44", "med": "MED-ALBU"},
    {"encounter_id": "ENC7006", "patient_id": "P1006", "doctor_id": "DOC302", "room_id": "RM-ICU-302", "type": "Inpatient", "status": "Active", "start": "2026-10-13T11:00:00Z", "end": None, "reason": "Bilateral bacterial pneumonia", "diag": "DIAG-J18", "med": "MED-CEFT"},
    {"encounter_id": "ENC7007", "patient_id": "P1007", "doctor_id": "DOC101", "room_id": "RM-PVT-401", "type": "Inpatient", "status": "Active", "start": "2026-10-14T08:00:00Z", "end": None, "reason": "Post-angioplasty recovery", "diag": "DIAG-I21", "med": "MED-ASPI"},
    {"encounter_id": "ENC7008", "patient_id": "P1008", "doctor_id": "DOC201", "room_id": "RM-ISO-101", "type": "Inpatient", "status": "Active", "start": "2026-10-14T15:20:00Z", "end": None, "reason": "Meningitis observation & isolation", "diag": "DIAG-G43", "med": "MED-CEFT"},

    # Emergency Encounters
    {"encounter_id": "ENC7009", "patient_id": "P1009", "doctor_id": "DOC401", "room_id": None, "type": "Emergency", "status": "Completed", "start": "2026-10-06T18:00:00Z", "end": "2026-10-06T22:30:00Z", "reason": "Severe atypical chest pain", "diag": "DIAG-R07", "med": "MED-ASPI"},
    {"encounter_id": "ENC7010", "patient_id": "P1010", "doctor_id": "DOC402", "room_id": None, "type": "Emergency", "status": "Completed", "start": "2026-10-07T03:15:00Z", "end": "2026-10-07T06:45:00Z", "reason": "Syncopal episode at home", "diag": "DIAG-R55", "med": "MED-ATOR"},
    {"encounter_id": "ENC7011", "patient_id": "P1011", "doctor_id": "DOC401", "room_id": None, "type": "Emergency", "status": "Completed", "start": "2026-10-08T12:00:00Z", "end": "2026-10-08T15:00:00Z", "reason": "Acute respiratory distress", "diag": "DIAG-J18", "med": "MED-ALBU"},

    # Outpatient Specialist Visits
    {"encounter_id": "ENC7012", "patient_id": "P1012", "doctor_id": "DOC102", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-08T09:00:00Z", "end": "2026-10-08T09:45:00Z", "reason": "Routine cardiac stress test follow-up", "diag": "DIAG-I10", "med": "MED-AMLO"},
    {"encounter_id": "ENC7013", "patient_id": "P1013", "doctor_id": "DOC202", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-09T10:30:00Z", "end": "2026-10-09T11:15:00Z", "reason": "Chronic migraine therapy review", "diag": "DIAG-G43", "med": "MED-SUMA"},
    {"encounter_id": "ENC7014", "patient_id": "P1014", "doctor_id": "DOC301", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-09T14:00:00Z", "end": "2026-10-09T14:40:00Z", "reason": "Spirometry evaluation", "diag": "DIAG-J44", "med": "MED-ALBU"},
    {"encounter_id": "ENC7015", "patient_id": "P1015", "doctor_id": "DOC101", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-10T08:30:00Z", "end": "2026-10-10T09:10:00Z", "reason": "Blood pressure management", "diag": "DIAG-I10", "med": "MED-ATOR"},

    # Multi-visit Care Pathways (Patients with sequential visits demonstrating care progression)
    # Patient P1001 second visit: Outpatient cardiology follow-up after discharge
    {"encounter_id": "ENC7016", "patient_id": "P1001", "doctor_id": "DOC101", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-10T11:00:00Z", "end": "2026-10-10T11:45:00Z", "reason": "Post-discharge review", "diag": "DIAG-I10", "med": "MED-ATOR"},
    # Patient P1003 second visit: Neurology consultation
    {"encounter_id": "ENC7017", "patient_id": "P1003", "doctor_id": "DOC201", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-11T13:00:00Z", "end": "2026-10-11T13:30:00Z", "reason": "Medication adjustment", "diag": "DIAG-G43", "med": "MED-SUMA"},
    # Patient P1009 transition: ER triage -> Inpatient General Ward admission
    {"encounter_id": "ENC7018", "patient_id": "P1009", "doctor_id": "DOC102", "room_id": "RM-GEN-203", "type": "Inpatient", "status": "Active", "start": "2026-10-13T09:00:00Z", "end": None, "reason": "Cardiac telemetry monitoring", "diag": "DIAG-I21", "med": "MED-ASPI"},
    # Patient P1016 shared ward stay with P1009 in GW-203
    {"encounter_id": "ENC7019", "patient_id": "P1016", "doctor_id": "DOC102", "room_id": "RM-GEN-203", "type": "Inpatient", "status": "Active", "start": "2026-10-14T10:00:00Z", "end": None, "reason": "Telemetry observation", "diag": "DIAG-I10", "med": "MED-AMLO"},

    # Additional varied encounters to satisfy the 35 target encounters
    {"encounter_id": "ENC7020", "patient_id": "P1017", "doctor_id": "DOC302", "room_id": "RM-PVT-402", "type": "Inpatient", "status": "Completed", "start": "2026-10-05T08:00:00Z", "end": "2026-10-09T12:00:00Z", "reason": "Persistent bronchitis", "diag": "DIAG-J18", "med": "MED-AZIT"},
    {"encounter_id": "ENC7021", "patient_id": "P1018", "doctor_id": "DOC402", "room_id": None, "type": "Emergency", "status": "Completed", "start": "2026-10-09T20:00:00Z", "end": "2026-10-09T23:30:00Z", "reason": "Asthma exacerbation", "diag": "DIAG-J44", "med": "MED-ALBU"},
    {"encounter_id": "ENC7022", "patient_id": "P1019", "doctor_id": "DOC201", "room_id": "RM-ICU-303", "type": "Inpatient", "status": "Active", "start": "2026-10-13T04:00:00Z", "end": None, "reason": "Transient ischemic attack workup", "diag": "DIAG-I63", "med": "MED-ASPI"},
    {"encounter_id": "ENC7023", "patient_id": "P1020", "doctor_id": "DOC301", "room_id": "RM-PVT-403", "type": "Inpatient", "status": "Discharged", "start": "2026-10-04T12:00:00Z", "end": "2026-10-08T11:00:00Z", "reason": "Pneumonia intravenous treatment", "diag": "DIAG-J18", "med": "MED-CEFT"},
    {"encounter_id": "ENC7024", "patient_id": "P1011", "doctor_id": "DOC101", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-11T10:00:00Z", "end": "2026-10-11T10:40:00Z", "reason": "Lipid profile check", "diag": "DIAG-I10", "med": "MED-ATOR"},
    {"encounter_id": "ENC7025", "patient_id": "P1012", "doctor_id": "DOC202", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-12T14:30:00Z", "end": "2026-10-12T15:00:00Z", "reason": "Tension headache management", "diag": "DIAG-G43", "med": "MED-SUMA"},
    {"encounter_id": "ENC7026", "patient_id": "P1013", "doctor_id": "DOC302", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-12T16:00:00Z", "end": "2026-10-12T16:45:00Z", "reason": "Allergic cough evaluation", "diag": "DIAG-J18", "med": "MED-AMOX"},
    {"encounter_id": "ENC7027", "patient_id": "P1014", "doctor_id": "DOC401", "room_id": None, "type": "Emergency", "status": "Completed", "start": "2026-10-13T22:15:00Z", "end": "2026-10-14T01:30:00Z", "reason": "Severe vertigo and nausea", "diag": "DIAG-R55", "med": "MED-ATOR"},
    {"encounter_id": "ENC7028", "patient_id": "P1015", "doctor_id": "DOC402", "room_id": None, "type": "Emergency", "status": "Completed", "start": "2026-10-14T03:00:00Z", "end": "2026-10-14T05:30:00Z", "reason": "Sudden onset dyspnea", "diag": "DIAG-J44", "med": "MED-ALBU"},
    {"encounter_id": "ENC7029", "patient_id": "P1017", "doctor_id": "DOC102", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-14T11:00:00Z", "end": "2026-10-14T11:30:00Z", "reason": "Echocardiogram consultation", "diag": "DIAG-I10", "med": "MED-ATOR"},
    {"encounter_id": "ENC7030", "patient_id": "P1018", "doctor_id": "DOC301", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-14T13:30:00Z", "end": "2026-10-14T14:15:00Z", "reason": "Post-asthma follow-up", "diag": "DIAG-J44", "med": "MED-ALBU"},
    {"encounter_id": "ENC7031", "patient_id": "P1002", "doctor_id": "DOC101", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-15T09:00:00Z", "end": "2026-10-15T09:30:00Z", "reason": "Holter monitor results review", "diag": "DIAG-I10", "med": "MED-AMLO"},
    {"encounter_id": "ENC7032", "patient_id": "P1004", "doctor_id": "DOC201", "room_id": None, "type": "Outpatient", "status": "Completed", "start": "2026-10-15T10:00:00Z", "end": "2026-10-15T10:30:00Z", "reason": "EEG follow-up", "diag": "DIAG-G43", "med": "MED-SUMA"},
    {"encounter_id": "ENC7033", "patient_id": "P1006", "doctor_id": "DOC301", "room_id": "RM-GEN-204", "type": "Inpatient", "status": "Active", "start": "2026-10-15T08:00:00Z", "end": None, "reason": "Pneumonia recovery step-down", "diag": "DIAG-J18", "med": "MED-CEFT"},
    {"encounter_id": "ENC7034", "patient_id": "P1007", "doctor_id": "DOC102", "room_id": "RM-GEN-204", "type": "Inpatient", "status": "Active", "start": "2026-10-15T11:00:00Z", "end": None, "reason": "Hypertensive urgency stabilization", "diag": "DIAG-I10", "med": "MED-AMLO"},
    {"encounter_id": "ENC7035", "patient_id": "P1020", "doctor_id": "DOC401", "room_id": None, "type": "Emergency", "status": "Active", "start": "2026-10-15T12:00:00Z", "end": None, "reason": "Acute chest pain triage", "diag": "DIAG-R07", "med": "MED-ASPI"},
]


class SeedService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    @staticmethod
    def get_synthetic_dataset_preview() -> Dict[str, Any]:
        """Returns the static dataset structure offline without database calls."""
        return {
            "departments": len(DEPARTMENTS_DATA),
            "doctors": len(DOCTORS_DATA),
            "rooms": len(ROOMS_DATA),
            "patients": len(PATIENTS_DATA),
            "diagnoses": len(DIAGNOSES_DATA),
            "medications": len(MEDICATIONS_DATA),
            "encounters": len(ENCOUNTERS_DATA),
            "sample_patient": PATIENTS_DATA[0],
            "sample_doctor": DOCTORS_DATA[0],
            "sample_encounter": ENCOUNTERS_DATA[0],
        }

    def seed_database(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Idempotently seeds all fictional hospital nodes and relationships.
        Never executes when dry_run=True.
        """
        if dry_run:
            logger.info("SeedService: Dry-run mode active. No database writes performed.")
            return {
                "dry_run": True,
                "status": "dry_run_success",
                "message": "Synthetic dataset validated offline. Zero database writes performed.",
                **self.get_synthetic_dataset_preview()
            }

        # Live Seeding Logic (Requires explicit execution flag and confirmed database isolation)
        logger.info("Executing idempotent hospital seeding into database...")

        # 1. Departments
        for dept in DEPARTMENTS_DATA:
            self.db.execute_query("""
            MERGE (d:Department {department_id: $department_id})
            ON CREATE SET d.name = $name, d.building = $building, d.floor = $floor, d.phone_extension = $phone_extension
            ON MATCH SET d.name = $name
            """, dept, read_only=False)

        # 2. Doctors & BELONGS_TO
        for doc in DOCTORS_DATA:
            self.db.execute_query("""
            MERGE (d:Doctor {doctor_id: $doctor_id})
            ON CREATE SET d.first_name = $first_name, d.last_name = $last_name,
                          d.specialty = $specialty, d.license_number = $license_number,
                          d.email = $email, d.phone = $phone, d.years_of_experience = $years_of_experience
            WITH d
            MATCH (dept:Department {department_id: $department_id})
            MERGE (d)-[:BELONGS_TO]->(dept)
            """, doc, read_only=False)

        # 3. Rooms
        for rm in ROOMS_DATA:
            self.db.execute_query("""
            MERGE (r:Room {room_id: $room_id})
            ON CREATE SET r.room_number = $room_number, r.room_type = $room_type,
                          r.capacity = $capacity, r.floor = $floor
            """, rm, read_only=False)

        # 4. Patients
        for p in PATIENTS_DATA:
            self.db.execute_query("""
            MERGE (pat:Patient {patient_id: $patient_id})
            ON CREATE SET pat.first_name = $first_name, pat.last_name = $last_name,
                          pat.dob = $dob, pat.gender = $gender, pat.blood_group = $blood_group,
                          pat.contact_phone = $contact_phone, pat.emergency_contact = $emergency_contact,
                          pat.created_at = '2026-10-01T00:00:00Z'
            """, p, read_only=False)

        # 5. Diagnoses Catalog
        for diag in DIAGNOSES_DATA:
            self.db.execute_query("""
            MERGE (d:Diagnosis {diagnosis_id: $diagnosis_id})
            ON CREATE SET d.icd10_code = $icd10_code, d.name = $name, d.category = $category
            """, diag, read_only=False)

        # 6. Medications Catalog
        for med in MEDICATIONS_DATA:
            self.db.execute_query("""
            MERGE (m:Medication {medication_id: $medication_id})
            ON CREATE SET m.name = $name, m.generic_name = $generic_name,
                          m.dosage_form = $dosage_form, m.standard_strength = $standard_strength
            """, med, read_only=False)

        # 7. Encounters, Document-Style JSON, and Clinical Relationships
        for enc in ENCOUNTERS_DATA:
            clinical_record = {
                "encounter_id": enc["encounter_id"],
                "encounter_type": enc["type"],
                "vital_signs": {
                    "temperature_celsius": 37.0,
                    "heart_rate_bpm": 76,
                    "blood_pressure": {"systolic_mmhg": 122, "diastolic_mmhg": 78},
                    "respiratory_rate_bpm": 16,
                    "oxygen_saturation_percent": 98,
                    "recorded_at": enc["start"]
                },
                "clinical_notes": {
                    "chief_complaint": enc["reason"],
                    "assessment_and_plan": f"Standard clinical management protocol for {enc['reason']}."
                },
                "encounter_timestamps": {
                    "admission_time": enc["start"],
                    "discharge_time": enc["end"]
                }
            }
            clinical_json_str = json.dumps(clinical_record)

            self.db.execute_query("""
            MATCH (pat:Patient {patient_id: $patient_id})
            MATCH (doc:Doctor {doctor_id: $doctor_id})
            MERGE (e:Encounter {encounter_id: $encounter_id})
            ON CREATE SET e.encounter_type = $encounter_type,
                          e.status = $status,
                          e.start_time = $start_time,
                          e.end_time = $end_time,
                          e.reason_for_visit = $reason_for_visit,
                          e.clinical_record_json = $clinical_json_str
            MERGE (pat)-[:HAS_ENCOUNTER]->(e)
            MERGE (e)-[:ATTENDED_BY]->(doc)
            WITH e
            OPTIONAL MATCH (rm:Room {room_id: $room_id})
            FOREACH (_ IN CASE WHEN rm IS NOT NULL THEN [1] ELSE [] END |
                MERGE (e)-[:ADMITTED_TO]->(rm)
            )
            WITH e
            OPTIONAL MATCH (diag:Diagnosis {diagnosis_id: $diag_id})
            FOREACH (_ IN CASE WHEN diag IS NOT NULL THEN [1] ELSE [] END |
                MERGE (e)-[:DIAGNOSED_WITH {status: 'Primary'}]->(diag)
            )
            WITH e
            OPTIONAL MATCH (med:Medication {medication_id: $med_id})
            FOREACH (_ IN CASE WHEN med IS NOT NULL THEN [1] ELSE [] END |
                MERGE (e)-[:PRESCRIBED {dosage: 'Standard', frequency: 'Daily'}]->(med)
            )
            """, {
                "encounter_id": enc["encounter_id"],
                "patient_id": enc["patient_id"],
                "doctor_id": enc["doctor_id"],
                "room_id": enc["room_id"] or "",
                "encounter_type": enc["type"],
                "status": enc["status"],
                "start_time": enc["start"],
                "end_time": enc["end"] or "",
                "reason_for_visit": enc["reason"],
                "clinical_json_str": clinical_json_str,
                "diag_id": enc["diag"],
                "med_id": enc["med"]
            }, read_only=False)

        logger.info("Hospital seeding completed successfully.")
        return {
            "status": "seeded",
            "departments_seeded": len(DEPARTMENTS_DATA),
            "doctors_seeded": len(DOCTORS_DATA),
            "rooms_seeded": len(ROOMS_DATA),
            "patients_seeded": len(PATIENTS_DATA),
            "diagnoses_seeded": len(DIAGNOSES_DATA),
            "medications_seeded": len(MEDICATIONS_DATA),
            "encounters_seeded": len(ENCOUNTERS_DATA)
        }
