"""
Pydantic schemas for WebSocket messages.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal, Union
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
    SYNC_DATA = "sync_data"
    TELEMETRY_UPDATE = "telemetry_update"


# ── Client → Server ─────────────────────────────────────
class ClientMessage(BaseModel):
    type: ClientMessageType
    id: str | None = None
    payload: Union[dict[str, Any], list[Any]] = Field(default_factory=dict)


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


class SyncStat(BaseModel):
    label: str
    value: str


class SyncField(BaseModel):
    type: str = "info"
    key: str
    label: str
    value: Any = None
    min: float | None = None
    max: float | None = None
    unit: str | None = None
    options: list[str] | None = None


class SyncSettingsGroup(BaseModel):
    title: str
    fields: list[SyncField] = Field(default_factory=list)


class RemoteCommandPayload(BaseModel):
    """Payload embedded in a SyncShortcut to tell the PC what to execute on tap."""
    action: str
    target: str | None = None
    params: dict[str, Any] | None = None
    shortcut_id: str | None = Field(default=None, alias="shortcutId")


class SyncShortcut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    label: str
    icon: str
    size: Literal["small", "wide", "tall", "big"] = "small"
    subtitle: str | None = None
    detail: str | None = None
    value: Any = None
    unit: str | None = None
    min: float | None = None
    max: float | None = None
    action_type: Literal["status", "toggle", "slider", "chips"] | None = Field(default=None, alias="actionType")
    options: list[str] | None = None
    logs: list[str] | None = None
    stats: list[SyncStat] | None = None
    progress_value: float | None = Field(default=None, alias="progressValue")
    progress_label: list[str] | None = Field(default=None, alias="progressLabel")
    settings_groups: list[SyncSettingsGroup] | None = Field(default=None, alias="settingsGroups")
    command: RemoteCommandPayload | None = None
    image_url: str | None = Field(default=None, alias="imageUrl")


class SyncCategory(BaseModel):
    id: str
    name: str
    color: str
    icon: str
    shortcuts: list[SyncShortcut] = Field(default_factory=list)


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
