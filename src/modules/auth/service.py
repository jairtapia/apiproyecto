"""
Auth service — business logic for registration, login, token refresh, logout.
"""
from datetime import datetime, timedelta, timezone

from src.config import settings
from src.models.session import Session
from src.models.user import User
from src.utils.errors import BadRequestError, ConflictError, UnauthorizedError
from src.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


async def register_user(email: str, username: str, password: str) -> User:
    """Register a new user. Raises ConflictError if email/username taken."""
    existing_email = await User.find_one(User.email == email)
    if existing_email:
        raise ConflictError("Email already registered")

    existing_username = await User.find_one(User.username == username)
    if existing_username:
        raise ConflictError("Username already taken")

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
    )
    await user.insert()
    return user


async def login_user(
    email: str,
    password: str,
    user_agent: str = "",
    ip_address: str = "",
) -> dict:
    """
    Authenticate user, create session, return tokens.
    """
    user = await User.find_one(User.email == email)
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    # Create tokens
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh = create_refresh_token(token_data)

    # Persist session
    session = Session(
        user_id=str(user.id),
        refresh_token=refresh,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    await session.insert()

    return {
        "access_token": access_token,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


async def refresh_tokens(refresh_token: str) -> dict:
    """Rotate refresh token and issue a new access token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    # Find the active session
    session = await Session.find_one(
        Session.refresh_token == refresh_token,
        Session.is_active == True,  # noqa: E712
    )
    if not session:
        raise UnauthorizedError("Session not found or revoked")

    user = await User.get(payload["sub"])
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    # Revoke old session
    session.is_active = False
    await session.save()

    # Issue new tokens
    token_data = {"sub": str(user.id), "username": user.username}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    # Create new session
    new_session = Session(
        user_id=str(user.id),
        refresh_token=new_refresh,
        user_agent=session.user_agent,
        ip_address=session.ip_address,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    await new_session.insert()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


async def logout_user(user_id: str, refresh_token: str | None = None):
    """
    Revoke sessions. If refresh_token is given, revoke that one session.
    Otherwise, revoke ALL sessions for the user.
    """
    if refresh_token:
        session = await Session.find_one(
            Session.user_id == user_id,
            Session.refresh_token == refresh_token,
            Session.is_active == True,  # noqa: E712
        )
        if session:
            session.is_active = False
            await session.save()
    else:
        # Logout from all devices
        sessions = await Session.find(
            Session.user_id == user_id,
            Session.is_active == True,  # noqa: E712
        ).to_list()
        for s in sessions:
            s.is_active = False
            await s.save()
