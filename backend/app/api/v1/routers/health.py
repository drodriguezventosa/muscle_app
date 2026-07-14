"""Liveness and readiness probes (required by Cloud Run and Docker healthchecks)."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


# GET + HEAD: uptime monitors (e.g. UptimeRobot) ping with HEAD by default, so
# the probes must answer HEAD too — otherwise they'd 405 and read as "down".
@router.api_route("/health", methods=["GET", "HEAD"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return 200 if the process is alive."""
    return {"status": "ok"}


@router.api_route("/ready", methods=["GET", "HEAD"], summary="Readiness probe")
async def ready() -> dict[str, str]:
    """Return 200 when the app is ready to serve traffic.

    TODO: check downstream dependencies (database, LLM provider) once wired.
    """
    return {"status": "ready"}
