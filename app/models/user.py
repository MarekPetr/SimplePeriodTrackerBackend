from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    gender: str  # "woman" or "man"


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: Optional[str] = None
    hashed_password: str
    partner_id: Optional[str] = None
    qr_code_token: Optional[str] = None
    sharing_settings: dict = {"share_periods": True, "share_ovulation": True, "share_notes": True}
    created_at: datetime

    class Config:
        populate_by_name = True


class UserResponse(UserBase):
    id: str
    partner_id: Optional[str] = None
    sharing_settings: dict
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
