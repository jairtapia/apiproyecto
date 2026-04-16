"""
Pydantic schemas for WebSocket messages.
"""
from pydantic import BaseModel, Field
from typing import Any
from enum import Enum


# ── Message types ────────────────────────────────────────
class ClientMessageType(str, Enum):
    NLP_INPUT = "nlp_input"
    EXECUTE_PLAN = "execute_plan"
    CANCEL_PLAN = "cancel_plan"
    PING = "ping"
    APP_FOCUSED = "app_focused"
    APP_OPENED = "app_opened"
    SYSTEM_STATS = "system_stats"
    SYNC_DATA = "sync_data"
    REMOTE_COMMAND = "remote_command"


class ServerMessageType(str, Enum):
    CONNECTED = "connected"
    ACTION_PLAN = "action_plan"
    ACTION_STARTED = "action_started"
    ACTION_RESULT = "action_result"
    PLAN_COMPLETE = "plan_complete"
    ERROR = "error"
    PONG = "pong"
    REMOTE_COMMAND = "remote_command"
    TELEMETRY_UPDATE = "telemetry_update"


# ── Client → Server ─────────────────────────────────────
class ClientMessage(BaseModel):
    type: ClientMessageType
    id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class NLPInputPayload(BaseModel):
    """Payload for nlp_input messages."""
    text: str | None = None
    audio_base64: str | None = None  # base64-encoded audio
    audio_format: str = "wav"        # wav, mp3, webm, etc.


# ── Server → Client ─────────────────────────────────────
class ServerMessage(BaseModel):
    type: ServerMessageType
    id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


# ── Action schemas ───────────────────────────────────────
class ActionItem(BaseModel):
    """One action in a plan."""
    name: str
    description: str
    params: dict[str, Any] = Field(default_factory=dict)
    order: int = 0


class ActionPlan(BaseModel):
    """A plan is a list of actions parsed from NLP input."""
    plan_id: str
    raw_input: str
    actions: list[ActionItem]
    confidence: float = 0.0
