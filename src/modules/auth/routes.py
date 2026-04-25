import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from src.middleware.auth import get_current_user
from src.models.user import User
from src.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    PairRequest,
)
from src.modules.auth import service
from src.utils.response import success_response
from src.utils.shared_state import active_pairing_codes

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _validate_pair_qr_payload(raw_qr_data: str | None) -> dict | None:
    if not raw_qr_data:
        return None

    try:
        qr_data = json.loads(raw_qr_data)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid QR payload") from exc

    expires_raw = qr_data.get("expires")
    if isinstance(expires_raw, str) and expires_raw:
        try:
            expires_at = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid QR expiration timestamp") from exc

        if expires_at < datetime.now(timezone.utc):
            raise ValueError("QR code expired")

    return qr_data


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Register a new user account."""
    user = await service.register_user(
        email=body.email,
        username=body.username,
        password=body.password,
    )
    return success_response(
        data=UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            roles=user.roles,
        ).model_dump(),
        message="User registered successfully",
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    """Authenticate and receive JWT tokens."""
    tokens = await service.login_user(
        email=body.email,
        password=body.password,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else "",
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    """Exchange a valid refresh token for new tokens (rotation)."""
    tokens = await service.refresh_tokens(body.refresh_token)
    return tokens


@router.post("/logout")
async def logout(
    body: RefreshRequest | None = None,
    user: User = Depends(get_current_user),
):
    """
    Logout the current session (if refresh_token provided)
    or logout from ALL devices (if no body).
    """
    await service.logout_user(
        user_id=str(user.id),
        refresh_token=body.refresh_token if body else None,
    )
    return success_response(message="Logged out successfully")


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return success_response(
        data=UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            roles=user.roles,
        ).model_dump()
    )


@router.post("/register-pair")
async def register_pair(body: PairRequest, user: User = Depends(get_current_user)):
    """Register a pairing code for the user (from desktop)."""
    active_pairing_codes[str(user.id)] = body.code
    return success_response(message="Pairing code registered")


@router.post("/pair")
async def pair_device(body: PairRequest, user: User = Depends(get_current_user)):
    """Verify pairing code from mobile device."""
    try:
        _validate_pair_qr_payload(body.qr_data)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(exc)},
        )

    user_id = str(user.id)
    stored_code = active_pairing_codes.get(user_id)
    
    if stored_code and body.code == stored_code:
        # Success! Clear the code after use
        del active_pairing_codes[user_id]
        
        return success_response(
            data={"deviceId": f"MOBILE-{user_id[:8]}"},
            message="Device paired successfully"
        )

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "Invalid or expired pairing code",
        },
    )
