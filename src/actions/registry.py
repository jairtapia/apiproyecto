"""
Action Registry — Central registration of all executable actions.

To add a new action:
1. Create a function with signature: async def my_action(params: dict, user_id: str) -> dict
2. Register it: registry.register("my_action", my_action, "Description")
"""
from typing import Callable, Awaitable
from dataclasses import dataclass, field


@dataclass
class RegisteredAction:
    name: str
    handler: Callable[..., Awaitable[dict]]
    description: str
    required_params: list[str] = field(default_factory=list)


class ActionRegistry:
    """Singleton registry of all available actions."""

    def __init__(self):
        self._actions: dict[str, RegisteredAction] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Awaitable[dict]],
        description: str = "",
        required_params: list[str] | None = None,
    ):
        """Register an action handler."""
        self._actions[name] = RegisteredAction(
            name=name,
            handler=handler,
            description=description,
            required_params=required_params or [],
        )

    def get(self, name: str) -> RegisteredAction | None:
        return self._actions.get(name)

    def list_actions(self) -> list[dict]:
        """List all registered actions (for docs/NLP context)."""
        return [
            {
                "name": a.name,
                "description": a.description,
                "required_params": a.required_params,
            }
            for a in self._actions.values()
        ]

    def has(self, name: str) -> bool:
        return name in self._actions


# Global singleton
registry = ActionRegistry()


def load_default_actions():
    """Load all built-in action definitions."""
    from src.actions.definitions import sample_actions  # noqa: F401
    from src.actions.definitions.desktop_relay import load_relay_actions
    load_relay_actions()
