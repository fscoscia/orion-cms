"""Authenticate a remote call by its API key."""

from django.core.cache import cache
from django.utils import timezone

from orion.mcp.models import ApiKey, hash_token

USED_WRITE_INTERVAL = 60  # seconds between writes of a key's last use


def authenticate(request):
    """The usable key of the request, or None for any reason it cannot be used.

    A missing, unknown, expired or revoked key, and one whose user is gone, inactive
    or a superuser, all give the same answer: nothing tells the caller which it was.
    """
    header = request.META.get("HTTP_AUTHORIZATION", "")
    scheme, _separator, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        return None
    key = (
        ApiKey.objects.select_related("user").filter(key_hash=hash_token(token)).first()
    )
    if key is None or key.status != "active":
        return None
    if not key.user.is_active or key.user.is_superuser:
        return None
    return key


def record_use(key):
    """Note that the key was used, writing at most once a minute per key."""
    if cache.add(f"orion_mcp_used_{key.pk}", 1, USED_WRITE_INTERVAL):
        ApiKey.objects.filter(pk=key.pk).update(last_used_at=timezone.now())
