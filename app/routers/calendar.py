from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.user import UserInDB
from app.services.cycle_calculator import CycleCalculator

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month", response_model=List[Dict[str, Any]])
async def get_month_data(
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
    
    # Get all notes for this month
    first_day_dt = datetime.combine(first_day, datetime.min.time())
    last_day_dt = datetime.combine(last_day, datetime.max.time())

    # Get all cycles for this user within the current month (sorted by date ascending for prediction)
    cycles_cursor = db.cycles.find(
        {"user_id": current_user.id, "is_predicted": False, "period_start_date": { "$lte": last_day_dt }, "period_end_date": { "$gte": first_day_dt} }
    ).sort("period_start_date", 1)

    actual_cycles = await cycles_cursor.to_list(length=None)

    # Generate predictions for this month
    predicted_cycle: dict = CycleCalculator.predict_next_cycle(
        actual_cycles,
    )
    # Combine actual and predicted cycles
    cycles: list = actual_cycles
    if predicted_cycle:
        cycles.append(predicted_cycle)

    notes_cursor = db.notes.find({
        "user_id": current_user.id,
        "date": {
            "$gte": first_day_dt,
            "$lte": last_day_dt
        }
    })
    notes = await notes_cursor.to_list(length=None)
    # Extract just the date part from datetime for comparison
    note_dates = {note["date"].date() for note in notes}

    if predicted_cycle:
        # Build set of predicted period days for fast lookup
        predicted_period_days = set()
        cycle_start: datetime = predicted_cycle["period_start_date"]
        cycle_end: datetime = predicted_cycle.get("period_end_date")
        if cycle_start and cycle_end:
            period_days = CycleCalculator.calculate_period_days(
                cycle_start.date(),
                predicted_cycle.get("period_length", 5)
            )
            predicted_period_days.update(period_days)

    # Build day info array
    day_info_list = []
    current_day = first_day
    
    while current_day <= last_day:
        # Use CycleCalculator to determine day type
        day_type = CycleCalculator.get_day_type(current_day, cycles)
        # Check if this is a predicted period day
        is_predicted = day_type == "period" and current_day in predicted_period_days

        day_info = {
            "date": current_day.isoformat(),
            "type": day_type,
            "isPredicted": is_predicted,
            "hasNote": current_day in note_dates
        }

        day_info_list.append(day_info)
        current_day += timedelta(days=1)

    return day_info_list
