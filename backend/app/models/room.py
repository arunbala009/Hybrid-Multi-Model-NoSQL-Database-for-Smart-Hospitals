"""
Room Data Models
================
Pydantic schemas for inpatient rooms, bed capacity, and ward types.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class RoomBase(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=20, example="102-A")
    room_type: str = Field(..., description="ICU, General Ward, Private, or Isolation", example="ICU")
    capacity: int = Field(1, ge=1, le=10, example=2)
    floor: Optional[int] = Field(1, example=2)


class RoomCreate(RoomBase):
    room_id: Optional[str] = Field(None, example="RM102")


class RoomResponse(RoomBase):
    room_id: str = Field(..., example="RM102")
    current_occupancy: Optional[int] = 0
    is_available: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class RoomListResponse(BaseModel):
    total: int
    items: List[RoomResponse]
