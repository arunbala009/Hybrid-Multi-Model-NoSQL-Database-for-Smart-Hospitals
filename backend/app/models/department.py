"""
Department Data Models
======================
Pydantic schemas for Department divisions.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Cardiology")
    building: Optional[str] = Field("Main Wing", example="Block A")
    floor: Optional[int] = Field(1, example=3)
    phone_extension: Optional[str] = Field(None, example="x4010")


class DepartmentCreate(DepartmentBase):
    department_id: Optional[str] = Field(None, example="DEP01")


class DepartmentResponse(DepartmentBase):
    department_id: str = Field(..., example="DEP01")
    doctor_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentListResponse(BaseModel):
    total: int
    items: List[DepartmentResponse]
