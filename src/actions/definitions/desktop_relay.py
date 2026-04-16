"""
Desktop Relay Actions — Handlers that forward commands to the user's connected desktop client.
"""
from src.actions.registry import registry
from src.websocket.connection import manager
from src.schemas.ws import ServerMessage, ServerMessageType

async def relay_to_desktop(action_name: str, params: dict, user_id: str) -> dict:
    """Relays a command to the desktop client via WebSocket."""
    
    # Create the command packet the desktop app expects
    command_payload = {
        "action": action_name,
        "params": params,
        "requestId": params.get("requestId", "server-relay"),
        "target": params.get("target") or params.get("app_name") or params.get("query")
    }

    # Wrap in a ServerMessage
    msg = ServerMessage(
        type=ServerMessageType.REMOTE_COMMAND,
        payload=command_payload
    )

    # Send to user's connections (the desktop client will pick it up)
    if manager.is_connected(user_id):
        await manager.send_to_user(user_id=user_id, message=msg)
        return {"status": "relayed", "action": action_name}
    else:
        return {"status": "failed", "error": "No desktop client connected for this user"}

# Register common desktop actions as relays
desktop_actions = [
    "open_app", "close_app", "volume_up", "volume_down", "volume_mute",
    "brightness_up", "brightness_down", "lock_screen", "screenshot",
    "minimize_all", "maximize_window", "minimize_window", "list_apps", "list_running"
]

def load_relay_actions():
    for action in desktop_actions:
        # We use a closure to capture the action name
        async def make_handler(a=action):
            return lambda params, user_id: relay_to_desktop(a, params, user_id)
        
        # Registration
        registry.register(
            name=action,
            handler=lambda p, u, a=action: relay_to_desktop(a, p, u),
            description=f"Relays '{action}' to the connected desktop device."
        )
