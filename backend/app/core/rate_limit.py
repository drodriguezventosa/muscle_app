"""Shared rate limiter (OWASP A04: throttle expensive/public endpoints)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

limiter = Limiter(key_func=get_remote_address)

# Per-route limit string, e.g. "60/minute", built from configuration.
RATE_LIMIT = f"{get_settings().rate_limit_per_minute}/minute"
