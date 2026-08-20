"""Health check endpoint tests.

These are the most basic tests ensuring the FastAPI app starts and
responds to health probes.  They do not require any external services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


class TestHealthCheck:
    """Tests for /health endpoint."""

    async def test_health_check_returns_ok(self, client: AsyncClient) -> None:
        """GET /health should return 200 with status=ok."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "soma-workspace-agent"

    async def test_readiness_check_returns_ready(self, client: AsyncClient) -> None:
        """GET /health/ready should return 200 with status=ready."""
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
