"""Aggregates feature routers served under the /api/v1 prefix.

Health/readiness probes are mounted at the root in `app.main`, not here, so
that orchestrators (Cloud Run, Docker) can reach them without the version prefix.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Feature routers (muscles, exercises, chat) are registered here as they land.
# Example:
#   from app.api.v1.routers import muscles
#   api_router.include_router(muscles.router)
