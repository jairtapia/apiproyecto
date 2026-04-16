"""
WebSocket route and message handler.
Handles the full lifecycle: auth → message routing → NLP → action execution.
"""
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from src.utils.security import decode_token
from src.websocket.connection import manager
from src.schemas.ws import (
    ClientMessage,
    ClientMessageType,
    ServerMessage,
    ServerMessageType,
    NLPInputPayload,
)
from src.nlp import process_input
from src.actions.executor import execute_plan
from src.utils.shared_state import user_sync_data

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for pending plans (per user)
# In production, use Redis or a dedicated store
_pending_plans: dict[str, dict] = {}  # plan_id → {plan, user_id}


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """
    WebSocket endpoint.

    Connect with: ws://host/ws?token=<jwt_access_token>
    """
    # ── Authentication ───────────────────────────────
    await websocket.accept()
    
    if not token:
        logger.warning(f"WS connection rejected: Missing token")
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_token(token)
    if not payload:
        logger.warning(f"WS connection rejected: Invalid token or expired (Token: {token[:20]}...)")
        await websocket.close(code=4001, reason="Invalid token or expired")
        return
        
    if payload.get("type") != "access":
        logger.warning(f"WS connection rejected: Wrong token type {payload.get('type')}")
        await websocket.close(code=4001, reason="Invalid token type")
        return

    user_id = payload.get("sub")
    username = payload.get("username", "unknown")

    if not user_id:
        logger.warning(f"WS connection rejected: No user_id in payload")
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # ── Connect ──────────────────────────────────────
    if user_id not in manager._connections:
        manager._connections[user_id] = []
    manager._connections[user_id].append(websocket)
    
    logger.info(f"WebSocket connected: {username} ({user_id})")
    await manager.send_to_ws(
        websocket,
        ServerMessage(
            type=ServerMessageType.CONNECTED,
            id=str(uuid4()),
            payload={"user_id": user_id, "username": username},
        ),
    )

    try:
        while True:
            # ── Receive message ──────────────────────
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
                msg = ClientMessage(**data)
            except Exception as e:
                await manager.send_to_ws(
                    websocket,
                    ServerMessage(
                        type=ServerMessageType.ERROR,
                        payload={"error": f"Invalid message format: {e}"},
                    ),
                )
                continue

            # ── Route message ────────────────────────
            await _handle_message(websocket, user_id, msg)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WS disconnected: user={username} ({user_id})")
    except Exception as e:
        manager.disconnect(websocket, user_id)
        logger.error(f"WS error for user={username}: {e}")


async def _handle_message(websocket: WebSocket, user_id: str, msg: ClientMessage):
    """Route a client message to the appropriate handler."""

    match msg.type:
        # ── Ping ─────────────────────────────────────
        case ClientMessageType.PING:
            await manager.send_to_ws(
                websocket,
                ServerMessage(type=ServerMessageType.PONG, id=msg.id),
            )

        # ── NLP Input ────────────────────────────────
        case ClientMessageType.NLP_INPUT:
            await _handle_nlp_input(websocket, user_id, msg)

        # ── Execute Plan ─────────────────────────────
        case ClientMessageType.EXECUTE_PLAN:
            await _handle_execute_plan(websocket, user_id, msg)

        # ── Cancel Plan ──────────────────────────────
        case ClientMessageType.CANCEL_PLAN:
            await _handle_cancel_plan(websocket, user_id, msg)

        # ── Telemetry (Relay to other devices) ───────
        case ClientMessageType.APP_FOCUSED | ClientMessageType.APP_OPENED | ClientMessageType.SYSTEM_STATS:
            logger.debug(f"Relaying telemetry: {msg.type} from {user_id}")
            await manager.send_to_user(
                user_id=user_id,
                message=ServerMessage(
                    type=ServerMessageType.TELEMETRY_UPDATE,
                    payload={
                        "telemetry_type": msg.type,
                        "data": msg.payload
                    }
                ),
                exclude=websocket
            )

        # ── Desktop Sync State ───────────────────────
        case ClientMessageType.SYNC_DATA:
            logger.info(f"Sync data received from {user_id}")
            # In-memory storage (user_id -> list of categories)
            user_sync_data[user_id] = msg.payload
            
            # Notify Android app that new sync data is available
            await manager.send_to_user(
                user_id=user_id,
                message=ServerMessage(
                    type=ServerMessageType.TELEMETRY_UPDATE,
                    payload={
                        "telemetry_type": "sync_refresh",
                        "data": msg.payload
                    }
                ),
                exclude=websocket
            )

        # ── Remote Execution ─────────────────────────
        case ClientMessageType.REMOTE_COMMAND:
            logger.info(f"Remote command from {user_id}: {msg.payload.get('action')}")
            # Relay to all other devices (specifically the desktop)
            # We map it to ServerMessageType.REMOTE_COMMAND so the desktop knows what it is
            await manager.send_to_user(
                user_id=user_id,
                message=ServerMessage(
                    type=ServerMessageType.REMOTE_COMMAND,
                    payload=msg.payload
                ),
                exclude=websocket
            )

        case _:
            await manager.send_to_ws(
                websocket,
                ServerMessage(
                    type=ServerMessageType.ERROR,
                    id=msg.id,
                    payload={"error": f"Unknown message type: {msg.type}"},
                ),
            )


async def _handle_nlp_input(websocket: WebSocket, user_id: str, msg: ClientMessage):
    """Process NLP input and return an action plan."""
    try:
        nlp_payload = NLPInputPayload(**msg.payload)
        plan = await process_input(
            text=nlp_payload.text,
            audio_base64=nlp_payload.audio_base64,
            audio_format=nlp_payload.audio_format,
        )

        # Store the plan for later execution
        _pending_plans[plan.plan_id] = {
            "plan": plan,
            "user_id": user_id,
        }

        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ACTION_PLAN,
                id=msg.id,
                payload=plan.model_dump(),
            ),
        )

    except Exception as e:
        logger.error(f"NLP processing error: {e}")
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ERROR,
                id=msg.id,
                payload={"error": str(e)},
            ),
        )


async def _handle_execute_plan(websocket: WebSocket, user_id: str, msg: ClientMessage):
    """Execute a previously proposed action plan."""
    plan_id = msg.payload.get("plan_id")
    if not plan_id or plan_id not in _pending_plans:
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ERROR,
                id=msg.id,
                payload={"error": "Plan not found or expired"},
            ),
        )
        return

    stored = _pending_plans.pop(plan_id)
    if stored["user_id"] != user_id:
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ERROR,
                id=msg.id,
                payload={"error": "Not authorized to execute this plan"},
            ),
        )
        return

    plan = stored["plan"]

    # Define callbacks for real-time progress
    async def on_start(action_name: str, order: int):
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ACTION_STARTED,
                payload={"plan_id": plan_id, "action": action_name, "order": order},
            ),
        )

    async def on_complete(action_name: str, order: int, result: dict):
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ACTION_RESULT,
                payload={
                    "plan_id": plan_id,
                    "action": action_name,
                    "order": order,
                    "status": "success",
                    "result": result,
                },
            ),
        )

    async def on_error(action_name: str, order: int, error: str):
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ACTION_RESULT,
                payload={
                    "plan_id": plan_id,
                    "action": action_name,
                    "order": order,
                    "status": "failed",
                    "error": error,
                },
            ),
        )

    # Execute!
    results = await execute_plan(
        plan_id=plan_id,
        actions=plan.actions,
        user_id=user_id,
        on_action_start=on_start,
        on_action_complete=on_complete,
        on_action_error=on_error,
    )

    # Send plan complete
    await manager.send_to_ws(
        websocket,
        ServerMessage(
            type=ServerMessageType.PLAN_COMPLETE,
            id=msg.id,
            payload={"plan_id": plan_id, "results": results},
        ),
    )


async def _handle_cancel_plan(websocket: WebSocket, user_id: str, msg: ClientMessage):
    """Cancel a pending plan."""
    plan_id = msg.payload.get("plan_id")
    if plan_id and plan_id in _pending_plans:
        stored = _pending_plans.pop(plan_id)
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ACTION_RESULT,
                id=msg.id,
                payload={"plan_id": plan_id, "status": "cancelled"},
            ),
        )
    else:
        await manager.send_to_ws(
            websocket,
            ServerMessage(
                type=ServerMessageType.ERROR,
                id=msg.id,
                payload={"error": "Plan not found"},
            ),
        )
