from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.models.user import UserInDB
from app.core.security import decode_access_token


class UserService:
    """Service for user-related operations."""

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserInDB]:
        """Get user by ID from database."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return UserInDB(
            id=str(user.id),
            email=user.email,
            gender=user.gender,
            hashed_password=user.hashed_password,
            partner_id=str(user.partner_id) if user.partner_id else None,
            qr_code_token=user.qr_code_token,
            sharing_settings=user.sharing_settings,
            created_at=user.created_at,
        )

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserInDB]:
        """Get user by email from database."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return UserInDB(
            id=str(user.id),
            email=user.email,
            gender=user.gender,
            hashed_password=user.hashed_password,
            partner_id=str(user.partner_id) if user.partner_id else None,
            qr_code_token=user.qr_code_token,
            sharing_settings=user.sharing_settings,
            created_at=user.created_at,
        )

    @staticmethod
    async def get_user_from_token(db: AsyncSession, token: str) -> Optional[UserInDB]:
        """
        Get user from JWT token.
        Validates token and retrieves user from database.
        """
        user_id = decode_access_token(token)
        if user_id is None:
            return None

        return await UserService.get_user_by_id(db, user_id)
