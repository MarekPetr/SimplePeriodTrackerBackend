from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class CycleBase(BaseModel):
    user_id: str
    period_start_date: date
    period_end_date: Optional[date] = None
    cycle_length: Optional[int] = None
    period_length: Optional[int] = None


class CycleCreate(BaseModel):
    period_start_date: date
    period_end_date: Optional[date] = None


class CycleInDB(CycleBase):
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class CycleResponse(BaseModel):
    id: str
    user_id: str
    period_start_date: date
    period_end_date: Optional[date]
    cycle_length: Optional[int]
    period_length: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

