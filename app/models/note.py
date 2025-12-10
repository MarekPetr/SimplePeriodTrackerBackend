from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


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
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class NoteResponse(BaseModel):
    id: str
    user_id: str
    date: datetime
    text: Optional[str]
    emoji_notes: List[EmojiNote]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
