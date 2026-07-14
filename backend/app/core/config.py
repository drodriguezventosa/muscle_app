"""Application settings, loaded from environment variables (12-factor)."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL


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
    # NoDecode stops pydantic-settings from JSON-decoding the env value, so the
    # validator below can accept a plain comma-separated string.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string (e.g. `http://a,http://b`) or a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # ---- Database ----
    postgres_user: str = "muscle"
    # No hardcoded credential: the password must come from the environment
    # (.env locally, GitHub secrets in CI, platform secrets in deploy).
    postgres_password: str = ""
    postgres_db: str = "muscle"
    postgres_host: str = "db"
    postgres_port: int = 5432
    # Managed Postgres (e.g. Neon) requires TLS; enable it in production.
    db_ssl: bool = False

    # ---- LLM ----
    # "stub" needs no external service (deterministic reply) — the zero-setup
    # default; switch to "ollama" (local, free) or "gemini" (free tier) via env.
    llm_provider: Literal["stub", "ollama", "gemini"] = "stub"
    llm_model: str = "llama3.1"
    ollama_base_url: str = "http://ollama:11434"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # ---- Embeddings ----
    # "fake" is deterministic and dependency-free (default); "sentence_transformers"
    # gives real semantic vectors but requires the optional `.[ai]` extra (torch).
    embedding_provider: Literal["fake", "sentence_transformers"] = "fake"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ---- Observability ----
    sentry_dsn: str = ""

    # ---- Rate limiting ----
    rate_limit_per_minute: int = 60

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy DSN from the discrete Postgres settings.

        Built with `URL.create` so special characters in the password (@, /, :, …)
        are percent-encoded correctly — managed providers like Neon issue such
        passwords.
        """
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (single source of truth)."""
    return Settings()
