from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, date
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.user import UserInDB
from app.models.note import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/{date}", response_model=NoteResponse)
def get_note_by_date(
    date: date,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Get note for a specific date."""
    # Convert date to datetime for MongoDB query
    date_dt = datetime.combine(date, datetime.min.time())

    note = db.notes.find_one({
        "user_id": current_user.id,
        "date": date_dt
    })

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date"
        )

    note["id"] = str(note["_id"])
    return NoteResponse(**note)


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_data: NoteCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Create a new note for a specific date."""
    # Convert date to datetime for MongoDB query
    date_dt = datetime.combine(note_data.date, datetime.min.time())

    # Check if note already exists for this date
    existing_note = db.notes.find_one({
        "user_id": current_user.id,
        "date": date_dt
    })

    if existing_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note already exists for this date. Use PUT to update."
        )

    # Create new note
    note_dict = note_data.model_dump()
    # Replace date with datetime for MongoDB
    note_dict["date"] = date_dt
    note_dict["user_id"] = current_user.id
    note_dict["created_at"] = datetime.utcnow()
    note_dict["updated_at"] = datetime.utcnow()

    result = db.notes.insert_one(note_dict)
    created_note = db.notes.find_one({"_id": result.inserted_id})

    created_note["id"] = str(created_note["_id"])
    return NoteResponse(**created_note)


@router.put("/{date}", response_model=NoteResponse)
def update_note(
    date: date,
    note_data: NoteUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Update an existing note."""
    # Convert date to datetime for MongoDB query
    date_dt = datetime.combine(date, datetime.min.time())

    # Find the note
    existing_note = db.notes.find_one({
        "user_id": current_user.id,
        "date": date_dt
    })

    if not existing_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date"
        )

    # Update only provided fields
    update_dict = note_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()

    db.notes.update_one(
        {"_id": existing_note["_id"]},
        {"$set": update_dict}
    )

    updated_note = db.notes.find_one({"_id": existing_note["_id"]})
    updated_note["id"] = str(updated_note["_id"])
    return NoteResponse(**updated_note)


@router.delete("/{date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    date: date,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Delete a note for a specific date."""
    # Convert date to datetime for MongoDB query
    date_dt = datetime.combine(date, datetime.min.time())

    result = db.notes.delete_one({
        "user_id": current_user.id,
        "date": date_dt
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date"
        )

    return None
