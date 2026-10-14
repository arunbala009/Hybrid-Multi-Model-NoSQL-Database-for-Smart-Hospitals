"""
Clinical Encounter and Document-Style Record Models
===================================================
Defines both the Graph Encounter entity and the embedded JSON document
structure for semi-structured medical charting (vitals, labs, notes).
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BloodPressure(BaseModel):
    systolic_mmhg: int = Field(..., ge=50, le=280, example=120)
    diastolic_mmhg: int = Field(..., ge=30, le=180, example=80)


class VitalSigns(BaseModel):
    temperature_celsius: float = Field(..., ge=32.0, le=44.0, example=37.2)
    heart_rate_bpm: int = Field(..., ge=30, le=250, example=78)
    blood_pressure: BloodPressure
    respiratory_rate_bpm: int = Field(..., ge=5, le=60, example=16)
    oxygen_saturation_percent: int = Field(..., ge=50, le=100, example=98)
    recorded_at: Optional[str] = Field(None, example="2026-10-15T08:30:00Z")


class ClinicalNotes(BaseModel):
    chief_complaint: str = Field(..., example="Chest discomfort and mild palpitations")
    history_of_present_illness: Optional[str] = None
    assessment_and_plan: str = Field(..., example="Rule out acute coronary syndrome; schedule ECG and troponin")
    discharge_summary: Optional[str] = None


class TestResultItem(BaseModel):
    panel: str = Field(..., example="Cardiac Panel")
    test_name: str = Field(..., example="Troponin I")
    value: Union[float, str] = Field(..., example=0.02)
    unit: Optional[str] = Field(None, example="ng/mL")
    reference_range: Optional[str] = Field(None, example="< 0.04")
    flag: Optional[str] = Field("NORMAL", example="NORMAL")
    reported_at: Optional[str] = None


class TreatmentSummary(BaseModel):
    procedures_performed: Optional[List[str]] = Field(default_factory=list, example=["ECG 12-Lead"])
    medications_administered: Optional[List[str]] = Field(default_factory=list, example=["Aspirin 325mg"])
    nursing_care_plan: Optional[str] = None
    dietary_instructions: Optional[str] = None


class ClinicalRecord(BaseModel):
    """The document-style JSON model embedded in Encounter."""
    vital_signs: Optional[VitalSigns] = None
    clinical_notes: Optional[ClinicalNotes] = None
    test_results: Optional[List[TestResultItem]] = Field(default_factory=list)
    treatment_summary: Optional[TreatmentSummary] = None
    encounter_timestamps: Optional[Dict[str, str]] = Field(default_factory=dict)


class EncounterBase(BaseModel):
    patient_id: str = Field(..., example="P1001")
    doctor_id: str = Field(..., example="DOC201")
    encounter_type: str = Field(..., description="Inpatient, Outpatient, or Emergency", example="Inpatient")
    status: str = Field("Active", description="Active, Discharged, Transferred, Completed", example="Active")
    start_time: str = Field(..., description="ISO-8601 timestamp", example="2026-10-15T09:00:00Z")
    end_time: Optional[str] = Field(None, description="ISO-8601 timestamp", example=None)
    reason_for_visit: str = Field(..., example="Acute chest pain evaluation")


class EncounterCreate(EncounterBase):
    encounter_id: Optional[str] = Field(None, example="ENC5001")
    room_id: Optional[str] = Field(None, description="Required for Inpatient encounters", example="RM102")
    primary_diagnosis: Optional[str] = Field(None, example="Essential Hypertension")
    primary_icd10: Optional[str] = Field(None, example="I10")
    prescriptions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    clinical_record: Optional[ClinicalRecord] = None


class EncounterUpdate(BaseModel):
    status: Optional[str] = None
    end_time: Optional[str] = None
    room_id: Optional[str] = None
    reason_for_visit: Optional[str] = None
    clinical_record: Optional[ClinicalRecord] = None


class EncounterResponse(EncounterBase):
    encounter_id: str = Field(..., example="ENC5001")
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    room_number: Optional[str] = None
    diagnoses: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    prescriptions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    clinical_record: Optional[Union[ClinicalRecord, Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)


class EncounterListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[EncounterResponse]
