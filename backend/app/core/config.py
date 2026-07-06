"""Application settings, loaded from environment variables (12-factor)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central, typed configuration. Never hardcode secrets; use env vars."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- App ----
    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "MuscleApp"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_json: bool = False

    # ---- CORS ----
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # ---- Database ----
    postgres_user: str = "muscle"
    # Dev-only default; real value is always injected via env in test/prod.
    postgres_password: str = "muscle_dev_pw"  # noqa: S105
    postgres_db: str = "muscle"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # ---- LLM ----
    llm_provider: Literal["ollama", "gemini"] = "ollama"
    llm_model: str = "llama3.1"
    ollama_base_url: str = "http://ollama:11434"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # ---- Embeddings ----
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ---- Observability ----
    sentry_dsn: str = ""

    # ---- Rate limiting ----
    rate_limit_per_minute: int = 60

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy DSN built from the discrete Postgres settings."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (single source of truth)."""
    return Settings()
