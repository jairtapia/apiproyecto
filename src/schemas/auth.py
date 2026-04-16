"""
Pydantic schemas for authentication requests/responses.
"""
from pydantic import BaseModel, EmailStr, Field


# ── Requests ─────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PairRequest(BaseModel):
    qr_data: str | None = None
    code: str


# ── Responses ────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    roles: list[str]

    class Config:
        from_attributes = True
