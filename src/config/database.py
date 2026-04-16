"""
MongoDB connection with Beanie ODM (async).
"""
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.config import settings

_client: AsyncIOMotorClient | None = None


async def connect_db():
    """Initialize MongoDB connection and Beanie document models."""
    global _client

    # Import all document models here
    from src.models.user import User
    from src.models.session import Session
    from src.models.action_log import ActionLog

    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_name = settings.MONGODB_URI.rsplit("/", 1)[-1].split("?")[0]

    await init_beanie(
        database=_client[db_name],
        document_models=[User, Session, ActionLog],
    )


async def close_db():
    """Close the MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None
