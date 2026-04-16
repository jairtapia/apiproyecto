"""
User document model.
"""
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import Field, EmailStr


class User(Document):
    email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    username: Indexed(str, unique=True)  # type: ignore[valid-type]
    hashed_password: str
    is_active: bool = True
    roles: list[str] = Field(default_factory=lambda: ["user"])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True,
                "roles": ["user"],
            }
        }
