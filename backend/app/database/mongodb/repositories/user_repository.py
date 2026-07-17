from typing import Optional
from bson import ObjectId
from app.database.mongodb.collections.user import User


class UserRepository:
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user document by its unique database ID."""
        try:
            return await User.get(ObjectId(user_id))
        except Exception:
            return await User.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user document by its registered email address."""
        return await User.find_one(User.email == email.lower().strip())

    async def create(self, user_data: dict) -> User:
        """Create and persist a new user document in MongoDB."""
        user = User(**user_data)
        user.email = user.email.lower().strip()
        await user.insert()
        return user

    async def update(self, user: User, update_data: dict) -> User:
        """Update fields of an existing user document and save it."""
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        await user.update_timestamp()
        return user
