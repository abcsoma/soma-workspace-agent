"""Application configuration via Pydantic Settings.

All configuration is loaded from environment variables (or .env file).
See .env.example for all available settings.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings.

    Loaded from environment variables. A `.env` file in the project root
    (backend/) is automatically picked up.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────
    app_name: str = "Soma Workspace Agent"
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Log level")
    log_file: str = Field(default="log.jsonl", description="Structured log file path (JSONL)")

    # ── DeepSeek API ───────────────────────────────────────────
    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API base URL (OpenAI-compatible)",
    )
    deepseek_model_flash: str = Field(
        default="deepseek-v4-flash",
        description="DeepSeek model for daily/fast tasks",
    )
    deepseek_model_pro: str = Field(
        default="deepseek-v4-pro",
        description="DeepSeek model for complex reasoning",
    )

    # ── PostgreSQL ─────────────────────────────────────────────
    pg_host: str = Field(default="localhost", description="PostgreSQL host")
    pg_port: int = Field(default=5432, description="PostgreSQL port")
    pg_user: str = Field(default="soma", description="PostgreSQL user")
    pg_password: str = Field(default="soma", description="PostgreSQL password")
    pg_db: str = Field(default="workspace_agent", description="PostgreSQL database name")

    @property
    def pg_dsn(self) -> str:
        """Async PostgreSQL connection string."""
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def pg_dsn_sync(self) -> str:
        """Sync PostgreSQL connection string (for Alembic)."""
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    # ── Redis ──────────────────────────────────────────────────
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database index")
    redis_password: str = Field(default="", description="Redis password")

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── Langfuse (W5+) ─────────────────────────────────────────
    langfuse_secret_key: str = Field(default="", description="Langfuse secret key")
    langfuse_public_key: str = Field(default="", description="Langfuse public key")
    langfuse_host: str = Field(default="http://localhost:3000", description="Langfuse host")

    # ── External APIs (W5+) ────────────────────────────────────
    opendota_api_base: str = Field(
        default="https://api.opendota.com/api",
        description="OpenDota API base URL",
    )
    steam_api_key: str = Field(default="", description="Steam Web API key")
    steam_id: str = Field(default="", description="Your Steam ID for Dota 2 personal data")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton)."""
    return Settings()
