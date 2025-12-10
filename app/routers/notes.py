from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.db.models import Note
from app.models.user import UserInDB
from app.models.note import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/{date}", response_model=NoteResponse)
async def get_note_by_date(
    date: datetime,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get note for a specific date."""
    stmt = select(Note).where(Note.user_id == current_user.id, Note.date == date)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date",
        )

    return NoteResponse(
        id=str(note.id),
        user_id=str(note.user_id),
        date=note.date,
        text=note.text,
        emoji_notes=note.emoji_notes,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new note for a specific date."""
    # Check if note already exists for this date
    stmt = select(Note).where(
        Note.user_id == current_user.id, Note.date == note_data.date
    )
    result = await db.execute(stmt)
    existing_note = result.scalar_one_or_none()

    if existing_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note already exists for this date. Use PUT to update.",
        )

    # Create new note
    note_dict = note_data.model_dump()
    note_dict["user_id"] = current_user.id

    # Convert emoji_notes from Pydantic models to dicts
    if "emoji_notes" in note_dict and note_dict["emoji_notes"]:
        note_dict["emoji_notes"] = [
            emoji.dict() if hasattr(emoji, "dict") else emoji
            for emoji in note_dict["emoji_notes"]
        ]

    new_note = Note(**note_dict)
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    return NoteResponse(
        id=str(new_note.id),
        user_id=str(new_note.user_id),
        date=new_note.date,
        text=new_note.text,
        emoji_notes=new_note.emoji_notes,
        created_at=new_note.created_at,
        updated_at=new_note.updated_at,
    )


@router.put("/{date}", response_model=NoteResponse)
async def update_note(
    date: datetime,
    note_data: NoteUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing note."""
    # Find the note
    stmt = select(Note).where(Note.user_id == current_user.id, Note.date == date)
    result = await db.execute(stmt)
    existing_note = result.scalar_one_or_none()

    if not existing_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date",
        )

    # Update only provided fields
    update_dict = note_data.model_dump(exclude_unset=True)

    # Convert emoji_notes from Pydantic models to dicts if provided
    if "emoji_notes" in update_dict and update_dict["emoji_notes"]:
        update_dict["emoji_notes"] = [
            emoji.dict() if hasattr(emoji, "dict") else emoji
            for emoji in update_dict["emoji_notes"]
        ]

    # Set updated_at timestamp (will be handled by onupdate in the model, but set here explicitly)
    update_dict["updated_at"] = datetime.utcnow()

    stmt = update(Note).where(Note.id == existing_note.id).values(**update_dict)
    await db.execute(stmt)
    await db.commit()

    # Fetch updated note
    stmt = select(Note).where(Note.id == existing_note.id)
    result = await db.execute(stmt)
    updated_note = result.scalar_one()

    return NoteResponse(
        id=str(updated_note.id),
        user_id=str(updated_note.user_id),
        date=updated_note.date,
        text=updated_note.text,
        emoji_notes=updated_note.emoji_notes,
        created_at=updated_note.created_at,
        updated_at=updated_note.updated_at,
    )


@router.delete("/{date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    date: datetime,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a note for a specific date."""
    stmt = delete(Note).where(Note.user_id == current_user.id, Note.date == date)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this date",
        )

    return None
