"""
Session document model — tracks active JWT sessions for logout/revocation.
"""
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import Field


class Session(Document):
    user_id: Indexed(str)  # type: ignore[valid-type]
    refresh_token: Indexed(str, unique=True)  # type: ignore[valid-type]
    user_agent: str = ""
    ip_address: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    class Settings:
        name = "sessions"
