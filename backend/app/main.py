"""FastAPI application factory and entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.api.v1.routers import health
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import limiter

HEALTH_DISCLAIMER = "Exercise recommendations are informational only and are not medical advice."


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app. Accepting settings makes testing easy."""
    settings = settings or get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=f"MuscleApp API. {HEALTH_DISCLAIMER}",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # Rate limiting (slowapi): per-route limits are declared with @limiter.limit.
    app.state.limiter = limiter
    # slowapi's handler is typed for RateLimitExceeded, not the base Exception.
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # CORS: strict allowlist from configuration (OWASP A05).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    # Health probes live at the root; feature endpoints under /api/v1.
    app.include_router(health.router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
