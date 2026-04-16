"""
WebSocket Connection Manager — Tracks active connections per user.
"""
import json
from fastapi import WebSocket
from src.schemas.ws import ServerMessage, ServerMessageType


class ConnectionManager:
    """Manages active WebSocket connections, grouped by user_id."""

    def __init__(self):
        # user_id → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a new connection."""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a connection from the registry."""
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws is not websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: str, message: ServerMessage, exclude: WebSocket | None = None):
        """Send a message to all connections of a specific user."""
        if user_id in self._connections:
            data = message.model_dump()
            for ws in self._connections[user_id]:
                if exclude and ws is exclude:
                    continue
                try:
                    await ws.send_json(data)
                except Exception:
                    pass  # Connection might be closing

    async def send_to_ws(self, websocket: WebSocket, message: ServerMessage):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message.model_dump())
        except Exception:
            pass

    async def broadcast(self, message: ServerMessage):
        """Send a message to ALL connected users."""
        data = message.model_dump()
        for user_id, connections in self._connections.items():
            for ws in connections:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass

    def get_connected_users(self) -> list[str]:
        """Get list of currently connected user IDs."""
        return list(self._connections.keys())

    def is_connected(self, user_id: str) -> bool:
        return user_id in self._connections and len(self._connections[user_id]) > 0


# Global singleton
manager = ConnectionManager()
