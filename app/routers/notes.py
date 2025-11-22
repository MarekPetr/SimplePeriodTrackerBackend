from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, date
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.user import UserInDB
from app.models.note import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/{note_date}", response_model=NoteResponse)
async def get_note_by_date(
    note_date: date,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Get note for a specific date."""
    note = await db.notes.find_one({
        "user_id": current_user.id,
        "note_date": note_date
    })

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date"
        )

    note["id"] = str(note["_id"])
    return NoteResponse(**note)


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Create a new note for a specific date."""
    # Check if note already exists for this date
    existing_note = await db.notes.find_one({
        "user_id": current_user.id,
        "note_date": note_data.note_date
    })

    if existing_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note already exists for this date. Use PUT to update."
        )

    # Create new note
    note_dict = note_data.model_dump()
    note_dict["user_id"] = current_user.id
    note_dict["created_at"] = datetime.utcnow()
    note_dict["updated_at"] = datetime.utcnow()

    result = await db.notes.insert_one(note_dict)
    created_note = await db.notes.find_one({"_id": result.inserted_id})

    created_note["id"] = str(created_note["_id"])
    return NoteResponse(**created_note)


@router.put("/{note_date}", response_model=NoteResponse)
async def update_note(
    note_date: date,
    note_data: NoteUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Update an existing note."""
    # Find the note
    existing_note = await db.notes.find_one({
        "user_id": current_user.id,
        "note_date": note_date
    })

    if not existing_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date"
        )

    # Update only provided fields
    update_dict = note_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()

    await db.notes.update_one(
        {"_id": existing_note["_id"]},
        {"$set": update_dict}
    )

    updated_note = await db.notes.find_one({"_id": existing_note["_id"]})
    updated_note["id"] = str(updated_note["_id"])
    return NoteResponse(**updated_note)


@router.delete("/{note_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_date: date,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_database),
):
    """Delete a note for a specific date."""
    result = await db.notes.delete_one({
        "user_id": current_user.id,
        "note_date": note_date
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date"
        )

    return None
