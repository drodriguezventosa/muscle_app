"""Application settings, loaded from environment variables (12-factor)."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, ValidationInfo, computed_field, field_validator
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
    # default; "ollama" (local, free), "gemini" (free tier), or "groq" (generous
    # free tier, no card — used in deploy) are selected via env.
    llm_provider: Literal["stub", "ollama", "gemini", "groq"] = "stub"
    llm_model: str = "llama3.1"
    ollama_base_url: str = "http://ollama:11434"
    gemini_api_key: str = ""
    # Kept current on purpose: measured 2026-07-27, gemini-2.0-flash answers 429
    # (its free-tier quota is gone) and gemini-2.5-flash 404s (retired). The
    # flash-lite line is alive and fast, and the adapter already tolerates
    # "thinking" parts. Production chat runs on Groq; this is for local use.
    gemini_model: str = "gemini-3.1-flash-lite"
    # Groq: OpenAI-compatible free tier (no card). Chat LLM for deploy, because
    # Gemini's free chat quota is too low (embeddings stay on Gemini).
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # ---- Embeddings ----
    # "fake" is deterministic and dependency-free (default); "jina" is the deploy
    # default (free tier, works from datacenter IPs — see ADR-0019); "gemini" also
    # works but its free tier rejects cloud egress IPs; "sentence_transformers"
    # gives real vectors locally but needs the `.[ai]` extra (torch).
    embedding_provider: Literal["fake", "jina", "gemini", "sentence_transformers"] = "fake"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Gemini embedding model (reuses `gemini_api_key`); truncated to embedding_dim.
    # gemini-embedding-001 was shut down by Google on 2026-07-14; gemini-embedding-2
    # is its replacement and supports flexible dimensions (128-3072), so the 384-dim
    # pgvector column stays as is. See docs/adr/0018-embedding-model-migration.md.
    gemini_embedding_model: str = "gemini-embedding-2"
    embedding_dim: int = 384
    # Jina AI (free tier, no card): reuses `embedding_dim` via Matryoshka
    # truncation, so switching provider needs no schema change.
    jina_api_key: str = ""
    jina_model: str = "jina-embeddings-v3"
    # One-shot switch: clear the stored catalog vectors at boot so they are
    # recomputed with the current model. Needed after changing embedding model,
    # because vectors from different models are not comparable. Keep it false
    # normally (a rebuild costs one API call per catalog row).
    embedding_rebuild: bool = False

    # ---- Vision (meal photo → estimated foods) ----
    # "stub" is deterministic and needs no service (default, dev/CI); "gemini"
    # calls the multimodal API. NOTE: Google's free tier is unreachable from
    # datacenter IPs (ADR-0019), so "gemini" works locally but not on Render.
    vision_provider: Literal["stub", "openrouter", "gemini"] = "stub"
    vision_model: str = "gemini-3.1-flash-lite"
    # OpenRouter (openrouter.ai, free tier, no card) is the deploy-capable option:
    # it accepts datacenter IPs. Measured 2026-07-27, `google/gemma-4-26b-a4b-it:free`
    # matched Gemini's 7/7 foods on a test plate but took ~16 s instead of ~2 s.
    openrouter_api_key: str = ""
    openrouter_vision_model: str = "google/gemma-4-26b-a4b-it:free"
    # Upload guardrail: plenty for a phone photo, small enough to bound memory
    # and the provider's token cost.
    vision_max_image_bytes: int = 5 * 1024 * 1024

    # ---- Coaching sign-in (trainers area) ----
    # Dev-only fallback: `_reject_default_secret_in_production` refuses to boot
    # with it when APP_ENV=production, so a real secret must be set there.
    jwt_secret: str = "dev-only-insecure-secret-change-me-in-prod"  # noqa: S105 - guarded
    jwt_expire_minutes: int = 480  # 8 h: long enough for a session, short enough to expire
    # Password of the seeded demo accounts. They exist so the app can be tried
    # without credentials, so this value is intentionally public — the accounts
    # only ever hold demo data.
    demo_password: str = "muscleapp-demo"  # noqa: S105 - public by design

    # ---- Cache ----
    # "memory" is in-process and zero-setup (default); "redis" uses an external
    # store (e.g. Upstash) via REDIS_URL. Falls back to memory if the URL is empty.
    cache_provider: Literal["memory", "redis"] = "memory"
    redis_url: str = ""
    cache_ttl_seconds: int = 86400  # 1 day

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

    @field_validator("jwt_secret")
    @classmethod
    def _reject_default_secret_in_production(cls, value: str, info: ValidationInfo) -> str:
        """Refuse the shipped fallback secret outside development (OWASP A05)."""
        if (
            info.data.get("app_env") == "production"
            and value == "dev-only-insecure-secret-change-me-in-prod"
        ):
            raise ValueError("JWT_SECRET must be set in production")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (single source of truth)."""
    return Settings()
