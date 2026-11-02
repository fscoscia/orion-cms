"""The visitor's address, behind the proxies the project declares."""

from django.conf import settings


def get_client_ip(request):
    """The address the request came from.

    With ORION_TRUSTED_PROXIES = N > 0 the site sits behind N proxies of its own, each
    appending the address it received to X-Forwarded-For: the visitor's is the Nth from
    the right. Anything further left was written by the visitor and is ignored.
    """
    proxies = getattr(settings, "ORION_TRUSTED_PROXIES", 0)
    remote_addr = request.META.get("REMOTE_ADDR", "")
    if proxies <= 0:
        return remote_addr
    forwarded = [
        address.strip()
        for address in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
        if address.strip()
    ]
    if not forwarded:
        return remote_addr
    return forwarded[-proxies] if len(forwarded) >= proxies else forwarded[0]
