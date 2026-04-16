"""
NLP Parser — Converts natural language text into a list of ActionItems.

This module is designed to be pluggable:
- "local" provider uses keyword-based parsing (no external API needed)
- "openai" provider sends text to OpenAI for intent extraction

Add new providers by creating a new parse function and registering it.
"""
import re
from src.config import settings
from src.schemas.ws import ActionItem


# ─────────────────────────────────────────────────────────
# Provider: local (keyword / rule-based)
# ─────────────────────────────────────────────────────────

# Map of known action keywords → action names
# Extend this dict as you add more actions to the registry
ACTION_KEYWORDS: dict[str, list[str]] = {
    "create_user": ["crear usuario", "registrar usuario", "nuevo usuario", "create user", "add user"],
    "delete_user": ["eliminar usuario", "borrar usuario", "delete user", "remove user"],
    "list_users": ["listar usuarios", "mostrar usuarios", "ver usuarios", "list users", "show users"],
    "send_email": ["enviar correo", "mandar email", "send email", "send mail"],
    "generate_report": ["generar reporte", "crear reporte", "generate report", "make report"],
    "update_settings": ["actualizar config", "cambiar configuración", "update settings"],
    "backup_database": ["respaldar base", "backup", "hacer respaldo", "backup database"],
    "restart_service": ["reiniciar servicio", "restart service", "reboot"],
}


async def _parse_local(text: str) -> tuple[list[ActionItem], float]:
    """
    Rule-based parser: scans the text for known keywords and builds an action list.
    Supports multiple actions separated by conjunctions (y, and, luego, después, then).
    """
    text_lower = text.lower().strip()

    # Split by conjunctions to detect multiple actions
    segments = re.split(r"\b(?:y|and|luego|después|then|,)\b", text_lower)

    actions: list[ActionItem] = []
    matched_count = 0

    for i, segment in enumerate(segments):
        segment = segment.strip()
        if not segment:
            continue

        for action_name, keywords in ACTION_KEYWORDS.items():
            for kw in keywords:
                if kw in segment:
                    # Extract potential params (text after the keyword)
                    param_text = segment.replace(kw, "").strip()
                    params = {"raw_text": param_text} if param_text else {}

                    actions.append(
                        ActionItem(
                            name=action_name,
                            description=f"Acción detectada: {kw}",
                            params=params,
                            order=i,
                        )
                    )
                    matched_count += 1
                    break  # One action per segment

    # Confidence is proportional to how many segments matched
    total_segments = max(len(segments), 1)
    confidence = matched_count / total_segments

    return actions, confidence


# ─────────────────────────────────────────────────────────
# Provider: openai (placeholder — requires OPENAI_API_KEY)
# ─────────────────────────────────────────────────────────
async def _parse_openai(text: str) -> tuple[list[ActionItem], float]:
    """
    Send text to OpenAI and parse the response into actions.
    Requires OPENAI_API_KEY in settings.

    TODO: Implement actual OpenAI call with structured output.
    """
    # This is the integration point for OpenAI.
    # You'd send a system prompt describing available actions,
    # then parse the structured JSON response.
    raise NotImplementedError(
        "OpenAI provider not yet implemented. "
        "Set NLP_PROVIDER=local or implement this method."
    )


# ─────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────
_PROVIDERS = {
    "local": _parse_local,
    "openai": _parse_openai,
}


async def parse_natural_language(text: str) -> tuple[list[ActionItem], float]:
    """Parse text using the configured NLP provider."""
    provider = settings.NLP_PROVIDER
    parser_fn = _PROVIDERS.get(provider)

    if not parser_fn:
        raise ValueError(f"Unknown NLP provider: {provider}. Available: {list(_PROVIDERS.keys())}")

    return await parser_fn(text)
