from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone


class EmojiNote(BaseModel):
    emoji: str
    description: str


class NoteBase(BaseModel):
    user_id: str
    date: datetime
    text: Optional[str] = None
    emoji_notes: List[EmojiNote] = []


class NoteCreate(BaseModel):
    date: datetime
    text: Optional[str] = None
    emoji_notes: List[EmojiNote] = []


class NoteUpdate(BaseModel):
    text: Optional[str] = None
    emoji_notes: Optional[List[EmojiNote]] = None


class NoteInDB(NoteBase):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    date: datetime
    text: Optional[str]
    emoji_notes: List[EmojiNote]
    created_at: datetime
    updated_at: datetime
