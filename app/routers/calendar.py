from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.user import UserInDB
from app.services.cycle_calculator import CycleCalculator

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month", response_model=List[Dict[str, Any]])
def get_month_data(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
) -> List[Dict[str, Any]]:
    """
    Get calendar data for a specific month including:
    - Period days
    - Ovulation days
    - Fertile window days
    - Which days have notes
    """
    # Calculate first and last day of the month
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Get all cycles for this user (sorted by most recent first)
    cycles_cursor = db.cycles.find({"user_id": current_user.id}).sort("start_date", -1)
    cycles = list(cycles_cursor)

    # Convert date objects to datetime for MongoDB query
    first_day_dt = datetime.combine(first_day, datetime.min.time())
    last_day_dt = datetime.combine(last_day, datetime.max.time())

    # Get all notes for this month
    notes_cursor = db.notes.find({
        "user_id": current_user.id,
        "note_date": {
            "$gte": first_day_dt,
            "$lte": last_day_dt
        }
    })
    notes = list(notes_cursor)
    note_dates = {note["note_date"] for note in notes}

    # Build day info array
    day_info_list = []
    current_day = first_day

    while current_day <= last_day:
        # Use CycleCalculator to determine day type
        day_type = CycleCalculator.get_day_type(current_day, cycles)

        day_info = {
            "date": current_day.isoformat(),
            "type": day_type,
            "isPredicted": False,  # TODO: Determine if from predicted cycle
            "hasNote": current_day in note_dates
        }

        day_info_list.append(day_info)
        current_day += timedelta(days=1)

    return day_info_list
