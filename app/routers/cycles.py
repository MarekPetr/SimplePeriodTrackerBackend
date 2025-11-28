from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, date
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.user import UserInDB
from app.models.cycle import CycleCreate, CycleResponse
from app.services.cycle_calculator import CycleCalculator
from typing import List

router = APIRouter(prefix="/cycles", tags=["cycles"])


@router.post("", response_model=CycleResponse, status_code=status.HTTP_201_CREATED)
async def create_cycle(
    cycle_data: CycleCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Create a new cycle (log period start)."""
    # Create new cycle
    cycle_dict = cycle_data.model_dump()

    # Convert date to datetime for MongoDB
    if cycle_dict.get("start_date"):
        start_date = cycle_dict["start_date"]
        cycle_dict["start_date"] = datetime.combine(start_date, datetime.min.time())

    if cycle_dict.get("end_date"):
        end_date = cycle_dict["end_date"]
        cycle_dict["end_date"] = datetime.combine(end_date, datetime.min.time())

    cycle_dict["user_id"] = current_user.id
    cycle_dict["is_predicted"] = False
    cycle_dict["created_at"] = datetime.utcnow()

    # Set default values for optional fields
    if "cycle_length" not in cycle_dict:
        cycle_dict["cycle_length"] = None
    if "period_length" not in cycle_dict:
        cycle_dict["period_length"] = None

    # Calculate period_length if end_date is provided
    if cycle_dict.get("end_date") and cycle_dict.get("start_date"):
        cycle_dict["period_length"] = (cycle_dict["end_date"] - cycle_dict["start_date"]).days + 1

    result = await db.cycles.insert_one(cycle_dict)
    created_cycle = await db.cycles.find_one({"_id": result.inserted_id})

    created_cycle["id"] = str(created_cycle["_id"])
    return CycleResponse(**created_cycle)


@router.get("", response_model=List[CycleResponse])
async def get_cycles(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Get all cycles for the current user."""
    cycles_cursor = db.cycles.find({"user_id": current_user.id}).sort("start_date", -1)
    cycles = await cycles_cursor.to_list(length=None)

    for cycle in cycles:
        cycle["id"] = str(cycle["_id"])
        # Ensure optional fields exist
        if "cycle_length" not in cycle:
            cycle["cycle_length"] = None
        if "period_length" not in cycle:
            cycle["period_length"] = None

    return [CycleResponse(**cycle) for cycle in cycles]


@router.put("/{cycle_id}", response_model=CycleResponse | None)
async def update_cycle(
    cycle_id: str,
    cycle_data: CycleCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Update an existing cycle (e.g., log period end)."""
    # Find the cycle
    existing_cycle = await db.cycles.find_one({
        "_id": ObjectId(cycle_id),
        "user_id": current_user.id
    })

    if not existing_cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )

    # Update cycle
    update_dict = cycle_data.model_dump(exclude_unset=True)

    # Convert date to datetime for MongoDB
    if update_dict.get("start_date"):
        start_date = update_dict["start_date"]
        update_dict["start_date"] = datetime.combine(start_date, datetime.min.time())

    if update_dict.get("end_date"):
        end_date = update_dict["end_date"]
        update_dict["end_date"] = datetime.combine(end_date, datetime.min.time())

    # Calculate period_length if end_date is provided
    if update_dict.get("end_date") and update_dict.get("start_date"):
        update_dict["period_length"] = (update_dict["end_date"] - update_dict["start_date"]).days + 1

    if update_dict["period_length"] == 0:
        await db.cycles.delete_one({
            "_id": ObjectId(cycle_id),
            "user_id": current_user.id
        })
        return None

    await db.cycles.update_one(
        {"_id": ObjectId(cycle_id)},
        {"$set": update_dict}
    )

    updated_cycle = await db.cycles.find_one({"_id": ObjectId(cycle_id)})
    updated_cycle["id"] = str(updated_cycle["_id"])
    # Ensure optional fields exist
    if "cycle_length" not in updated_cycle:
        updated_cycle["cycle_length"] = None
    if "period_length" not in updated_cycle:
        updated_cycle["period_length"] = None
    return CycleResponse(**updated_cycle)


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cycle(
    cycle_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Delete a cycle."""
    result = await db.cycles.delete_one({
        "_id": ObjectId(cycle_id),
        "user_id": current_user.id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )

    return None
