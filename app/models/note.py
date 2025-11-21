from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema):
        schema.update(type="string")
        return schema


class EmojiNote(BaseModel):
    emoji: str
    description: str


class NoteBase(BaseModel):
    user_id: str
    note_date: date
    text: Optional[str] = None
    emoji_notes: List[EmojiNote] = []


class NoteCreate(BaseModel):
    note_date: date
    text: Optional[str] = None
    emoji_notes: List[EmojiNote] = []


class NoteUpdate(BaseModel):
    text: Optional[str] = None
    emoji_notes: Optional[List[EmojiNote]] = None


class NoteInDB(NoteBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class NoteResponse(BaseModel):
    id: str
    user_id: str
    note_date: date
    text: Optional[str]
    emoji_notes: List[EmojiNote]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
