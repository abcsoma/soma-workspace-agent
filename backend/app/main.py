"""FastAPI application entry point.

W1: Minimal health-check endpoint + app scaffold.
Future iterations will add SSE chat, module REST APIs, and agent endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown hooks."""
    settings = get_settings()
    # W1: no external connections yet; placeholder for future DB/Redis init
    app.state.settings = settings
    yield
    # Shutdown: close connections (added in later iterations)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Personal Workspace Agent - AI Agent for daily productivity",
        lifespan=lifespan,
    )

    # CORS (relax for local dev; tighten in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health check ──────────────────────────────────────────
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Liveness probe. Returns OK if the service is up."""
        return {"status": "ok", "service": "soma-workspace-agent", "version": "0.1.0"}

    @app.get("/health/ready", tags=["system"])
    async def readiness_check() -> dict[str, str]:
        """Readiness probe. Checks if external dependencies are reachable.

        W1: always returns ready (no external deps yet).
        W2+: will check PostgreSQL, Redis, and DeepSeek API connectivity.
        """
        return {"status": "ready"}

    return app


# Module-level app instance for ``uvicorn app.main:app``
app = create_app()
