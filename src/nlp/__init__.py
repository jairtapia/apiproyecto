"""
NLP Pipeline — Entry point.
Orchestrates: audio → text → parse → action list.
"""
from src.nlp.parser import parse_natural_language
from src.nlp.audio_processor import transcribe_audio
from src.schemas.ws import ActionItem, ActionPlan
from uuid import uuid4


async def process_input(
    text: str | None = None,
    audio_base64: str | None = None,
    audio_format: str = "wav",
) -> ActionPlan:
    """
    Process natural language input (text or audio) into an ActionPlan.

    Flow:
    1. If audio is provided → transcribe to text
    2. Parse text into intents/actions
    3. Resolve into an ActionPlan
    """
    # Step 1: Audio → text (if applicable)
    if audio_base64 and not text:
        text = await transcribe_audio(audio_base64, audio_format)

    if not text:
        return ActionPlan(
            plan_id=str(uuid4()),
            raw_input="",
            actions=[],
            confidence=0.0,
        )

    # Step 2: Parse text → list of action items
    actions, confidence = await parse_natural_language(text)

    # Step 3: Build the plan
    plan = ActionPlan(
        plan_id=str(uuid4()),
        raw_input=text,
        actions=actions,
        confidence=confidence,
    )

    return plan
