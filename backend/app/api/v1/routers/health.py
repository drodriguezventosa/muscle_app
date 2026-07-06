"""Liveness and readiness probes (required by Cloud Run and Docker healthchecks)."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return 200 if the process is alive."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, str]:
    """Return 200 when the app is ready to serve traffic.

    TODO: check downstream dependencies (database, LLM provider) once wired.
    """
    return {"status": "ready"}
