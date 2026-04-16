"""
Standardized API response helpers.
"""
from typing import Any


def success_response(
    data: Any = None,
    message: str = "OK",
    meta: dict | None = None,
) -> dict:
    """Build a standardized success response."""
    resp = {"success": True, "message": message}
    if data is not None:
        resp["data"] = data
    if meta:
        resp["meta"] = meta
    return resp
