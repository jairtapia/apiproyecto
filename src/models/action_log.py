"""
ActionLog document — persists every action executed via the pipeline.
"""
from datetime import datetime, timezone
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field


class ActionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionLog(Document):
    user_id: Indexed(str)  # type: ignore[valid-type]
    plan_id: Indexed(str)  # type: ignore[valid-type]
    action_name: str
    action_params: dict = Field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    result: dict | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    class Settings:
        name = "action_logs"
