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


class CycleBase(BaseModel):
    user_id: str
    start_date: date
    end_date: Optional[date] = None
    cycle_length: Optional[int] = None
    period_length: Optional[int] = None


class CycleCreate(BaseModel):
    start_date: date
    end_date: Optional[date] = None


class CycleInDB(CycleBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CycleResponse(BaseModel):
    id: str
    user_id: str
    start_date: date
    end_date: Optional[date]
    cycle_length: Optional[int]
    period_length: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    predicted_start: date
    predicted_end: date
    ovulation_start: date
    ovulation_end: date
