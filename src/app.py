"""
FastAPI application factory.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.config.database import connect_db, close_db
from src.actions.registry import load_default_actions


def _setup_logging():
    """Configure structured logging."""
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    _setup_logging()
    logger = logging.getLogger("app")

    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    await connect_db()
    logger.info("MongoDB connected")

    load_default_actions()
    logger.info("Actions loaded")

    yield

    # Shutdown
    await close_db()
    logger.info("MongoDB disconnected")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="API escalable con gestión de usuarios, WebSocket y pipeline NLP para acciones",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ───────────────────────────────────────
    from src.modules.auth.routes import router as auth_router
    from src.modules.sync.routes import router as sync_router
    from src.websocket.handler import router as ws_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(sync_router, prefix="/api/v1")
    app.include_router(ws_router)

    # ── Health check ─────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "app": settings.APP_NAME}

    return app
