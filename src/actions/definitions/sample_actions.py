"""
Sample action definitions — demonstrates how to register actions.

Each action is an async function with signature:
    async def action_name(params: dict, user_id: str) -> dict

The returned dict is sent back to the client as the action result.
"""
import asyncio
from src.actions.registry import registry


# ─────────────────────────────────────────────────────────
# Action: list_users
# ─────────────────────────────────────────────────────────
async def list_users_action(params: dict, user_id: str) -> dict:
    """List all users in the system."""
    from src.models.user import User

    users = await User.find_all().to_list()
    return {
        "users": [
            {"id": str(u.id), "username": u.username, "email": u.email}
            for u in users
        ],
        "total": len(users),
    }


# ─────────────────────────────────────────────────────────
# Action: create_user
# ─────────────────────────────────────────────────────────
async def create_user_action(params: dict, user_id: str) -> dict:
    """Create a new user (via action pipeline)."""
    from src.modules.auth.service import register_user

    raw = params.get("raw_text", "")
    # In a real implementation, NLP would extract email/username/password
    return {
        "message": f"create_user action received with params: {raw}",
        "note": "Implement full param extraction from NLP context",
    }


# ─────────────────────────────────────────────────────────
# Action: delete_user
# ─────────────────────────────────────────────────────────
async def delete_user_action(params: dict, user_id: str) -> dict:
    """Delete a user (placeholder)."""
    return {"message": "delete_user action placeholder", "params": params}


# ─────────────────────────────────────────────────────────
# Action: send_email
# ─────────────────────────────────────────────────────────
async def send_email_action(params: dict, user_id: str) -> dict:
    """Send an email (placeholder — integrate with SMTP/SendGrid/etc.)."""
    await asyncio.sleep(0.5)  # simulate work
    return {"message": "Email sent (simulated)", "params": params}


# ─────────────────────────────────────────────────────────
# Action: generate_report
# ─────────────────────────────────────────────────────────
async def generate_report_action(params: dict, user_id: str) -> dict:
    """Generate a report (placeholder)."""
    await asyncio.sleep(1)  # simulate heavy work
    return {"message": "Report generated (simulated)", "report_id": "RPT-001"}


# ─────────────────────────────────────────────────────────
# Action: update_settings
# ─────────────────────────────────────────────────────────
async def update_settings_action(params: dict, user_id: str) -> dict:
    """Update system settings (placeholder)."""
    return {"message": "Settings updated (simulated)", "params": params}


# ─────────────────────────────────────────────────────────
# Action: backup_database
# ─────────────────────────────────────────────────────────
async def backup_database_action(params: dict, user_id: str) -> dict:
    """Backup database (placeholder)."""
    await asyncio.sleep(2)  # simulate long process
    return {"message": "Backup completed (simulated)", "backup_id": "BKP-001"}


# ─────────────────────────────────────────────────────────
# Action: restart_service
# ─────────────────────────────────────────────────────────
async def restart_service_action(params: dict, user_id: str) -> dict:
    """Restart a service (placeholder)."""
    await asyncio.sleep(0.5)
    return {"message": "Service restarted (simulated)"}


# ─────────────────────────────────────────────────────────
# Register all actions
# ─────────────────────────────────────────────────────────
registry.register("list_users", list_users_action, "List all users")
registry.register("create_user", create_user_action, "Create a new user", ["email", "username", "password"])
registry.register("delete_user", delete_user_action, "Delete a user", ["user_id"])
registry.register("send_email", send_email_action, "Send an email", ["to", "subject", "body"])
registry.register("generate_report", generate_report_action, "Generate a report")
registry.register("update_settings", update_settings_action, "Update system settings")
registry.register("backup_database", backup_database_action, "Backup the database")
registry.register("restart_service", restart_service_action, "Restart a service")
