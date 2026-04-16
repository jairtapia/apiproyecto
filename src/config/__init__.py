"""
Centralized configuration via pydantic-settings.
Reads from .env automatically.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────
    APP_NAME: str = "ActionAPI"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── MongoDB ──────────────────────────────────────
    MONGODB_URI: str = "mongodb://localhost:27017/action_api"

    # ── JWT ──────────────────────────────────────────
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── NLP ──────────────────────────────────────────
    NLP_PROVIDER: str = "local"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"

    # ── Audio ────────────────────────────────────────
    AUDIO_ENABLED: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
