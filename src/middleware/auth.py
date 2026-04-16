"""
Authentication dependency for FastAPI routes.
Extracts and validates the JWT from the Authorization header.
"""
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.models.user import User
from src.utils.errors import UnauthorizedError
from src.utils.security import decode_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> User:
    """Dependency: returns the authenticated User or raises 401."""
    if credentials is None:
        raise UnauthorizedError("Missing authorization header")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await User.get(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


async def require_roles(*roles: str):
    """Factory: returns a dependency that checks the user has at least one of the given roles."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if not any(r in user.roles for r in roles):
            raise UnauthorizedError("Insufficient permissions")
        return user

    return _check
