import logging
from fastapi import HTTPException, status
from app.database.mongodb.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse

logger = logging.getLogger("backend.modules.users")


class UsersModule:
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    async def get_user_profile(self, user_id: str) -> UserResponse:
        """Fetch the public profile schema of the requested user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"Profile fetch failed: User {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found."
            )
        
        return UserResponse.from_orm(user)
