"""Full-page cache for visitors without a session.

Entries are keyed by a generation: emptying the cache means starting a new generation,
so old entries become unreachable and expire on their own. The rest of the shared cache
(sessions, renditions, rate limits) is never touched.
"""

import hashlib
import time

from django.core.cache import cache
from django.db import transaction

GENERATION_KEY = "orion:page-generation"


def get_generation():
    generation = cache.get(GENERATION_KEY)
    if generation is None:
        # A timestamp, never a counter: if the key is evicted, values cannot repeat.
        cache.add(GENERATION_KEY, time.time_ns(), timeout=None)
        generation = cache.get(GENERATION_KEY)
    return generation


def clear_page_cache():
    """Start a new generation once the current transaction commits."""
    transaction.on_commit(
        lambda: cache.set(GENERATION_KEY, time.time_ns(), timeout=None)
    )


def generation_key(*parts):
    """A cache key that changes with the generation."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return f"orion:{get_generation()}:{digest}"
