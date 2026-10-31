"""Read the cache backend from a CACHE_URL, without extra dependencies."""

import hashlib
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

BACKENDS = {
    "file": "django.core.cache.backends.filebased.FileBasedCache",
    "redis": "django.core.cache.backends.redis.RedisCache",
    "rediss": "django.core.cache.backends.redis.RedisCache",
    "locmem": "django.core.cache.backends.locmem.LocMemCache",
    "dummy": "django.core.cache.backends.dummy.DummyCache",
}


def parse_cache_url(url: str, secret_key: str) -> dict:
    """Return the ``CACHES["default"]`` settings for ``url``.

    Empty means files in the system's temporary folder. Keys get a prefix derived from
    the secret key, so two projects on the same server never share entries.
    """
    scheme = urlsplit(url).scheme if url else "file"
    if scheme not in BACKENDS:
        schemes = ", ".join(f"{name}://" for name in BACKENDS)
        raise ImproperlyConfigured(
            f"CACHE_URL must start with one of {schemes}; got {url!r}."
        )
    config = {
        "BACKEND": BACKENDS[scheme],
        "KEY_PREFIX": hashlib.sha256(secret_key.encode()).hexdigest()[:12],
    }
    if scheme == "file":
        path = urlsplit(url).path if url else ""
        config["LOCATION"] = path or str(Path(tempfile.gettempdir()) / "orion-cache")
    elif scheme in ("redis", "rediss"):
        config["LOCATION"] = url
    return config
