"""Best-effort limits on the MCP endpoint, kept in Django's cache.

With several processes and a cache that is local to each one (the default), a limit
holds per process, not for the whole site. A shared cache (CACHE_URL) makes it exact.
"""

import time

from django.conf import settings
from django.core.cache import cache

FAILED_AUTH_LIMIT = 10  # failed attempts allowed per address in a window
FAILED_AUTH_WINDOW = 300  # seconds
RATE_WINDOW = 60  # seconds


def _hit(name, window):
    """Count one event in the current fixed window; return the count and the seconds
    left in the window."""
    now = time.time()
    index = int(now // window)
    key = f"orion_mcp_{name}_{index}"
    cache.add(key, 0, window + 5)
    try:
        count = cache.incr(key)
    except ValueError:  # the entry expired between add and incr
        cache.set(key, 1, window + 5)
        count = 1
    return count, max(1, int((index + 1) * window - now))


def _peek(name, window):
    now = time.time()
    index = int(now // window)
    return (
        cache.get(f"orion_mcp_{name}_{index}", 0),
        max(1, int((index + 1) * window - now)),
    )


def failed_auth_blocked_for(address):
    """Seconds a client address must wait after too many failed attempts, or 0."""
    count, left = _peek(f"fail_{address}", FAILED_AUTH_WINDOW)
    return left if count >= FAILED_AUTH_LIMIT else 0


def record_failed_auth(address):
    _hit(f"fail_{address}", FAILED_AUTH_WINDOW)


def rate_limited_for(key):
    """Count a request of the key; seconds to wait if it went over its minute, or 0."""
    count, left = _hit(f"rate_{key.pk}", RATE_WINDOW)
    return left if count > settings.ORION_MCP_RATE_LIMIT else 0
