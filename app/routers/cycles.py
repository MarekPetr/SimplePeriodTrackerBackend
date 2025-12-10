from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, date, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.db.models import Cycle
from app.models.user import UserInDB
from app.models.cycle import CycleCreate, CycleResponse
from app.services.cycle_calculator import CycleCalculator
from typing import List

router = APIRouter(prefix="/cycles", tags=["cycles"])


@router.post("", response_model=CycleResponse, status_code=status.HTTP_201_CREATED)
async def create_cycle(
    cycle_data: CycleCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new cycle (log period start)."""
    # Create new cycle
    cycle_dict = cycle_data.model_dump()

    # Convert date to datetime for database (using UTC)
    if cycle_dict.get("period_start_date"):
        period_start_date = cycle_dict["period_start_date"]
        cycle_dict["period_start_date"] = datetime.combine(
            period_start_date, datetime.min.time(), tzinfo=timezone.utc
        )

    if cycle_dict.get("period_end_date"):
        period_end_date = cycle_dict["period_end_date"]
        cycle_dict["period_end_date"] = datetime.combine(
            period_end_date, datetime.min.time(), tzinfo=timezone.utc
        )

    cycle_dict["user_id"] = current_user.id
    cycle_dict["is_predicted"] = False

    # Calculate period_length if period_end_date is provided
    if cycle_dict.get("period_end_date") and cycle_dict.get("period_start_date"):
        cycle_dict["period_length"] = (
            cycle_dict["period_end_date"] - cycle_dict["period_start_date"]
        ).days + 1

    new_cycle = Cycle(**cycle_dict)
    db.add(new_cycle)
    await db.commit()
    await db.refresh(new_cycle)

    return CycleResponse(
        id=str(new_cycle.id),
        user_id=str(new_cycle.user_id),
        period_start_date=new_cycle.period_start_date.date(),
        period_end_date=new_cycle.period_end_date.date() if new_cycle.period_end_date else None,
        cycle_length=new_cycle.cycle_length,
        period_length=new_cycle.period_length,
        created_at=new_cycle.created_at,
    )


@router.get("", response_model=List[CycleResponse])
async def get_cycles(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all cycles for the current user."""
    stmt = (
        select(Cycle)
        .where(Cycle.user_id == current_user.id)
        .order_by(Cycle.period_start_date.desc())
    )
    result = await db.execute(stmt)
    cycles = result.scalars().all()

    return [
        CycleResponse(
            id=str(c.id),
            user_id=str(c.user_id),
            period_start_date=c.period_start_date.date(),
            period_end_date=c.period_end_date.date() if c.period_end_date else None,
            cycle_length=c.cycle_length,
            period_length=c.period_length,
            created_at=c.created_at,
        )
        for c in cycles
    ]


@router.put("/{cycle_id}", response_model=CycleResponse | None)
async def update_cycle(
    cycle_id: str,
    cycle_data: CycleCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing cycle (e.g., log period end)."""
    # Find the cycle
    stmt = select(Cycle).where(Cycle.id == cycle_id, Cycle.user_id == current_user.id)
    result = await db.execute(stmt)
    existing_cycle = result.scalar_one_or_none()

    if not existing_cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cycle not found"
        )

    # Update cycle
    update_dict = cycle_data.model_dump(exclude_unset=True)

    # Convert date to datetime for database (using UTC)
    if update_dict.get("period_start_date"):
        period_start_date = update_dict["period_start_date"]
        update_dict["period_start_date"] = datetime.combine(
            period_start_date, datetime.min.time(), tzinfo=timezone.utc
        )

    if update_dict.get("period_end_date"):
        period_end_date = update_dict["period_end_date"]
        update_dict["period_end_date"] = datetime.combine(
            period_end_date, datetime.min.time(), tzinfo=timezone.utc
        )

    # Calculate period_length if period_end_date is provided
    if update_dict.get("period_end_date") and update_dict.get("period_start_date"):
        update_dict["period_length"] = (
            update_dict["period_end_date"] - update_dict["period_start_date"]
        ).days + 1

    if update_dict.get("period_length") == 0:
        # Delete cycle if period_length is 0
        stmt = delete(Cycle).where(Cycle.id == cycle_id, Cycle.user_id == current_user.id)
        await db.execute(stmt)
        await db.commit()
        return None

    stmt = (
        update(Cycle)
        .where(Cycle.id == cycle_id)
        .values(**update_dict)
    )
    await db.execute(stmt)
    await db.commit()

    # Fetch updated cycle
    stmt = select(Cycle).where(Cycle.id == cycle_id)
    result = await db.execute(stmt)
    updated_cycle = result.scalar_one()

    return CycleResponse(
        id=str(updated_cycle.id),
        user_id=str(updated_cycle.user_id),
        period_start_date=updated_cycle.period_start_date.date(),
        period_end_date=(
            updated_cycle.period_end_date.date() if updated_cycle.period_end_date else None
        ),
        cycle_length=updated_cycle.cycle_length,
        period_length=updated_cycle.period_length,
        created_at=updated_cycle.created_at,
    )


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cycle(
    cycle_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a cycle."""
    stmt = delete(Cycle).where(Cycle.id == cycle_id, Cycle.user_id == current_user.id)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cycle not found"
        )

    return None
