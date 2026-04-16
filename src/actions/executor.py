"""
Action Executor — Runs a plan's actions sequentially and reports progress.

Each action result is sent back via a callback so the WebSocket can
stream confirmations to the client in real time.
"""
from datetime import datetime, timezone
from typing import Callable, Awaitable

from src.actions.registry import registry
from src.models.action_log import ActionLog, ActionStatus
from src.schemas.ws import ActionItem


async def execute_plan(
    plan_id: str,
    actions: list[ActionItem],
    user_id: str,
    on_action_start: Callable | None = None,
    on_action_complete: Callable | None = None,
    on_action_error: Callable | None = None,
) -> list[dict]:
    """
    Execute a list of actions sequentially.

    Args:
        plan_id: Unique plan identifier
        actions: Ordered list of ActionItems to execute
        user_id: ID of the user who initiated the plan
        on_action_start: Callback(action_name, order) called before each action
        on_action_complete: Callback(action_name, order, result) called after success
        on_action_error: Callback(action_name, order, error) called on failure

    Returns:
        List of result dicts for each action
    """
    results = []

    for action in sorted(actions, key=lambda a: a.order):
        # Create a log entry
        log = ActionLog(
            user_id=user_id,
            plan_id=plan_id,
            action_name=action.name,
            action_params=action.params,
            status=ActionStatus.RUNNING,
        )
        await log.insert()

        # Notify: action starting
        if on_action_start:
            await on_action_start(action.name, action.order)

        # Look up the registered handler
        registered = registry.get(action.name)
        if not registered:
            error_msg = f"Action '{action.name}' not found in registry"
            log.status = ActionStatus.FAILED
            log.error = error_msg
            log.completed_at = datetime.now(timezone.utc)
            await log.save()

            if on_action_error:
                await on_action_error(action.name, action.order, error_msg)

            results.append({"action": action.name, "status": "failed", "error": error_msg})
            continue

        # Execute the action
        try:
            result = await registered.handler(action.params, user_id)

            log.status = ActionStatus.SUCCESS
            log.result = result
            log.completed_at = datetime.now(timezone.utc)
            await log.save()

            if on_action_complete:
                await on_action_complete(action.name, action.order, result)

            results.append({"action": action.name, "status": "success", "result": result})

        except Exception as e:
            error_msg = str(e)
            log.status = ActionStatus.FAILED
            log.error = error_msg
            log.completed_at = datetime.now(timezone.utc)
            await log.save()

            if on_action_error:
                await on_action_error(action.name, action.order, error_msg)

            results.append({"action": action.name, "status": "failed", "error": error_msg})

    return results
