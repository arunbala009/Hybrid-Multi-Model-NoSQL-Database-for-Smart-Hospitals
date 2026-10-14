"""
Rooms API Router
================
Endpoints for inpatient bed locations, room types, and live availability.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from backend.app.database import DatabaseManager, get_db
from backend.app.models.room import RoomResponse, RoomListResponse

router = APIRouter(prefix="/api/v1/rooms", tags=["Rooms & Beds"])


@router.get("", response_model=RoomListResponse, summary="List Hospital Rooms")
def list_rooms(
    room_type: Optional[str] = Query(None, description="Filter by type (ICU, General Ward, Private, Isolation)"),
    floor: Optional[int] = Query(None, description="Filter by floor level"),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves all hospital rooms, calculating current active occupancy."""
    where_clauses = []
    params = {}
    if room_type:
        where_clauses.append("r.room_type = $room_type")
        params["room_type"] = room_type
    if floor is not None:
        where_clauses.append("r.floor = $floor")
        params["floor"] = floor

    where_stmt = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    MATCH (r:Room)
    {where_stmt}
    OPTIONAL MATCH (r)<-[adm:ADMITTED_TO]-(e:Encounter)
    WHERE e.status = 'Active' AND (e.end_time IS NULL OR e.end_time = '')
    RETURN r.room_id AS room_id,
           r.room_number AS room_number,
           r.room_type AS room_type,
           r.capacity AS capacity,
           r.floor AS floor,
           count(DISTINCT e) AS current_occupancy,
           CASE WHEN count(DISTINCT e) >= r.capacity THEN false ELSE true END AS is_available
    ORDER BY r.floor ASC, r.room_number ASC
    """
    records, _ = db.execute_query(query, params)
    return {"total": len(records), "items": records}


@router.get("/{room_id}", response_model=RoomResponse, summary="Get Room Details")
def get_room(
    room_id: str = Path(..., example="RM-ICU-301"),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves details of a specific inpatient room."""
    query = """
    MATCH (r:Room {room_id: $room_id})
    OPTIONAL MATCH (r)<-[adm:ADMITTED_TO]-(e:Encounter)
    WHERE e.status = 'Active' AND (e.end_time IS NULL OR e.end_time = '')
    RETURN r.room_id AS room_id,
           r.room_number AS room_number,
           r.room_type AS room_type,
           r.capacity AS capacity,
           r.floor AS floor,
           count(DISTINCT e) AS current_occupancy,
           CASE WHEN count(DISTINCT e) >= r.capacity THEN false ELSE true END AS is_available
    """
    records, _ = db.execute_query(query, {"room_id": room_id})
    if not records or not records[0].get("room_id"):
        raise HTTPException(status_code=404, detail=f"Room '{room_id}' not found.")
    return records[0]
