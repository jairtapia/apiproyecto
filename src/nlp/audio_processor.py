"""
Audio Processor — Transcribes audio to text.

This is a placeholder module. To enable audio processing:
1. Set AUDIO_ENABLED=true in .env
2. Install the appropriate audio library (e.g., openai-whisper, google-cloud-speech)
3. Implement the transcription logic below.
"""
import base64
from src.config import settings


async def transcribe_audio(audio_base64: str, audio_format: str = "wav") -> str:
    """
    Transcribe base64-encoded audio into text.

    Args:
        audio_base64: Base64-encoded audio data
        audio_format: Audio format (wav, mp3, webm, etc.)

    Returns:
        Transcribed text string

    Integration points:
        - OpenAI Whisper API
        - Google Cloud Speech-to-Text
        - Azure Cognitive Services
        - Local Whisper model
    """
    if not settings.AUDIO_ENABLED:
        raise RuntimeError(
            "Audio processing is disabled. Set AUDIO_ENABLED=true in .env"
        )

    # Decode the audio to validate it's proper base64
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception as e:
        raise ValueError(f"Invalid base64 audio data: {e}")

    # ──────────────────────────────────────────────────
    # TODO: Implement actual transcription here.
    # Example with OpenAI Whisper API:
    #
    # import openai
    # client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    # audio_file = io.BytesIO(audio_bytes)
    # audio_file.name = f"audio.{audio_format}"
    # transcript = await client.audio.transcriptions.create(
    #     model="whisper-1",
    #     file=audio_file,
    # )
    # return transcript.text
    # ──────────────────────────────────────────────────

    raise NotImplementedError(
        "Audio transcription not yet implemented. "
        "Add your preferred speech-to-text provider here."
    )
