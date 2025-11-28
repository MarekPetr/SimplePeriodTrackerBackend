from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from app.models.user import UserCreate, UserInDB, UserResponse, Token, RefreshTokenRequest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.core.database import get_database
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    from bson import ObjectId
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Convert ObjectId to string for Pydantic
    user["id"] = str(user["_id"])
    return UserInDB(**user)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    from datetime import datetime
    db = get_database()

    # Check if user already exists
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Validate gender
    if user.gender not in ["woman", "man"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Gender must be 'woman' or 'man'"
        )

    # Create user
    user_dict = user.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["sharing_settings"] = {
        "share_periods": True,
        "share_ovulation": True,
        "share_notes": True,
    }
    user_dict["created_at"] = datetime.now().isoformat()

    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})

    return UserResponse(
        id=str(created_user["_id"]),
        email=created_user["email"],
        gender=created_user["gender"],
        partner_id=created_user.get("partner_id"),
        sharing_settings=created_user["sharing_settings"],
        created_at=created_user["created_at"],
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    user = await db.users.find_one({"email": form_data.username})

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user["_id"])}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user["_id"])})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    user_id = decode_refresh_token(request.refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        gender=current_user.gender,
        partner_id=current_user.partner_id,
        sharing_settings=current_user.sharing_settings,
        created_at=current_user.created_at,
    )


@router.put("/sharing-settings")
async def update_sharing_settings(
    settings: dict, current_user: UserInDB = Depends(get_current_user)
):
    db = get_database()

    # Validate settings
    valid_keys = {"share_periods", "share_ovulation", "share_notes"}
    if not all(key in valid_keys for key in settings.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sharing settings"
        )

    await db.users.update_one({"_id": current_user.id}, {"$set": {"sharing_settings": settings}})

    return {"message": "Sharing settings updated successfully"}
