from typing import Optional
from bson import ObjectId
from app.models.user import UserInDB
from app.core.security import decode_access_token


class UserService:
    """Service for user-related operations."""

    @staticmethod
    async def get_user_by_id(db, user_id: str) -> Optional[UserInDB]:
        """Get user by ID from database."""
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None

        user["id"] = str(user["_id"])
        return UserInDB(**user)

    @staticmethod
    async def get_user_by_email(db, email: str) -> Optional[UserInDB]:
        """Get user by email from database."""
        user = await db.users.find_one({"email": email})
        if not user:
            return None

        user["id"] = str(user["_id"])
        return UserInDB(**user)

    @staticmethod
    async def get_user_from_token(db, token: str) -> Optional[UserInDB]:
        """
        Get user from JWT token.
        Validates token and retrieves user from database.
        """
        user_id = decode_access_token(token)
        if user_id is None:
            return None

        return await UserService.get_user_by_id(db, user_id)
