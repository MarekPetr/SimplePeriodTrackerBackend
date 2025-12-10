from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.db.models import Cycle, Note
from app.models.user import UserInDB
from app.services.cycle_calculator import CycleCalculator

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month", response_model=List[Dict[str, Any]])
async def get_month_data(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

    first_day_dt = datetime.combine(first_day, datetime.min.time())
    last_day_dt = datetime.combine(last_day, datetime.max.time())

    # Get all cycles for this user within the current month (sorted by date ascending for prediction)
    stmt = (
        select(Cycle)
        .where(
            Cycle.user_id == current_user.id,
            Cycle.is_predicted == False,
            Cycle.period_start_date <= last_day_dt,
            Cycle.period_end_date >= first_day_dt,
        )
        .order_by(Cycle.period_start_date)
    )
    result = await db.execute(stmt)
    actual_cycles = result.scalars().all()

    # Convert SQLAlchemy objects to dict format for CycleCalculator
    cycles = []
    for c in actual_cycles:
        cycles.append(
            {
                "id": str(c.id),
                "user_id": str(c.user_id),
                "period_start_date": c.period_start_date,
                "period_end_date": c.period_end_date,
                "cycle_length": c.cycle_length,
                "period_length": c.period_length,
                "is_predicted": c.is_predicted,
                "created_at": c.created_at,
            }
        )

    # Get notes for the month
    stmt = select(Note).where(
        Note.user_id == current_user.id,
        Note.date >= first_day_dt,
        Note.date <= last_day_dt,
    )
    result = await db.execute(stmt)
    notes = result.scalars().all()

    # Extract just the date part from datetime for comparison
    note_dates = {note.date.date() for note in notes}

    # Build day info array
    day_info_list = []
    current_day = first_day

    while current_day <= last_day:
        # Use CycleCalculator to determine day type
        day_type = CycleCalculator.get_day_type(current_day, cycles)
        day_info = {
            "date": current_day.isoformat(),
            "type": day_type,
            "hasNote": current_day in note_dates,
        }

        day_info_list.append(day_info)
        current_day += timedelta(days=1)

    return day_info_list
