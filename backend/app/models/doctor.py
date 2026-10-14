"""
Doctor Data Models
==================
Pydantic schemas for Doctor entity validation and department affiliations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DoctorBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, example="Sarah")
    last_name: str = Field(..., min_length=1, max_length=50, example="Jenkins")
    specialty: str = Field(..., min_length=2, max_length=100, example="Cardiology")
    license_number: str = Field(..., min_length=3, max_length=50, example="MD-CARD-9921")
    email: Optional[str] = Field(None, example="s.jenkins@smarthospital.org")
    phone: Optional[str] = Field(None, example="+1-555-0211")
    years_of_experience: Optional[int] = Field(0, ge=0, example=12)


class DoctorCreate(DoctorBase):
    doctor_id: Optional[str] = Field(None, description="Optional custom doctor_id", example="DOC201")
    department_id: Optional[str] = Field(None, description="Department to affiliate physician with", example="DEP01")


class DoctorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    specialty: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    years_of_experience: Optional[int] = None
    department_id: Optional[str] = None


class DoctorResponse(DoctorBase):
    doctor_id: str = Field(..., example="DOC201")
    department_id: Optional[str] = None
    department_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DoctorListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[DoctorResponse]
