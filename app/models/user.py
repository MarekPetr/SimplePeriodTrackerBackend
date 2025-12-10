from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    gender: str  # "woman" or "man"


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = None
    hashed_password: str
    partner_id: Optional[str] = None
    qr_code_token: Optional[str] = None
    sharing_settings: dict = {"share_periods": True, "share_ovulation": True, "share_notes": True}
    created_at: datetime


class UserResponse(UserBase):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    partner_id: Optional[str] = None
    sharing_settings: dict
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
