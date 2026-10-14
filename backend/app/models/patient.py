"""
Patient Data Models
===================
Pydantic schemas for Patient entity validation, serialization, and API responses.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, example="John")
    last_name: str = Field(..., min_length=1, max_length=50, example="Doe")
    dob: str = Field(..., description="ISO-8601 date YYYY-MM-DD", example="1980-05-15")
    gender: str = Field(..., description="Male, Female, or Other", example="Male")
    blood_group: str = Field(..., description="ABO/Rh Blood Group", example="O+")
    contact_phone: Optional[str] = Field(None, example="+1-555-0199")
    emergency_contact: Optional[str] = Field(None, example="Jane Doe (+1-555-0198)")


class PatientCreate(PatientBase):
    patient_id: Optional[str] = Field(None, description="Optional custom patient_id (auto-generated if omitted)", example="P1001")


class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    contact_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None


class PatientResponse(PatientBase):
    patient_id: str = Field(..., example="P1001")
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[PatientResponse]
