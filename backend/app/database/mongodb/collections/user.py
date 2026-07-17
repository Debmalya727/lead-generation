from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import EmailStr, Field
from pymongo import IndexModel, ASCENDING


class User(Document):
    email: EmailStr = Field(..., description="Unique email address of the user")
    password_hash: str = Field(..., description="Bcrypt hashed password")
    full_name: str = Field(..., description="User's full display name")
    is_active: bool = Field(default=True, description="Indicates if the user profile is active")
    is_superuser: bool = Field(default=False, description="Indicates if user has admin privileges")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            IndexModel(
                [("email", ASCENDING)],
                unique=True,
                name="idx_user_email_unique"
            )
        ]

    async def update_timestamp(self) -> None:
        """Helper to update updated_at timestamp on save."""
        self.updated_at = datetime.now(timezone.utc)
        await self.save()
