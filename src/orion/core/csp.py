"""The content security policy of the public site, with a fresh nonce per response.

Wagtail's admin uses inline scripts, so it gets no policy: only the public site does.
"""

import hashlib
import re
import secrets

from django.conf import settings
from django.utils.http import quote_etag

NONCE = "'nonce'"
HEADER = "Content-Security-Policy"
REPORT_ONLY_HEADER = "Content-Security-Policy-Report-Only"

DEFAULT_POLICY = {
    "default-src": ["'self'"],
    # 'self' only serves browsers without 'strict-dynamic'; the others run nonced
    # scripts and whatever those load.
    "script-src": [NONCE, "'strict-dynamic'", "'self'"],
    # Leaflet, Wagtail's user bar and third-party snippets use inline styles.
    "style-src": ["'self'", "'unsafe-inline'"],
    # What analytics, pixels, chats and map tiles need, without listing hosts.
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'", "data:", "https:"],
    "connect-src": ["'self'", "https:"],
    "frame-src": ["'self'", "https:"],
    "media-src": ["'self'", "https:"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'self'"],
}


def new_nonce():
    return secrets.token_urlsafe(16)


def get_policy():
    """The default policy with the project's directives (ORION_CSP) over it."""
    return {**DEFAULT_POLICY, **getattr(settings, "ORION_CSP", {})}


def build_header(nonce):
    return "; ".join(
        " ".join(
            [directive, *(f"'nonce-{nonce}'" if v == NONCE else v for v in values)]
        )
        for directive, values in get_policy().items()
        if values is not None
    )


def get_header_name():
    if getattr(settings, "ORION_CSP_REPORT_ONLY", False):
        return REPORT_ONLY_HEADER
    return HEADER


def is_public_path(path):
    excluded = (
        f"/{settings.ORION_ADMIN_PATH}",
        settings.STATIC_URL,
        settings.MEDIA_URL,
    )
    return not path.startswith(
        tuple("/" + prefix.lstrip("/") for prefix in excluded if prefix)
    )


OPENING_TAG = re.compile(r"<(script|style)\b(?![^>]*\bnonce=)", re.IGNORECASE)


def add_nonce(html, nonce):
    """Add the nonce to every opening <script> and <style> tag that lacks one.

    Only for trusted HTML (Orion's templates, Wagtail's and code snippets pasted by
    people with the dedicated permission), never for what visitors send.
    """
    if not nonce:
        return html
    return OPENING_TAG.sub(lambda match: f'<{match.group(1)} nonce="{nonce}"', html)


class ContentSecurityPolicyMiddleware:
    """Gives public responses a nonce (request.csp_nonce) and the policy header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not is_public_path(request.path):
            return self.get_response(request)
        request.csp_nonce = new_nonce()
        response = self.get_response(request)
        name = get_header_name()
        if name not in response:
            response[name] = build_header(request.csp_nonce)
        if not response.streaming and not response.has_header("ETag"):
            # The same page renders with a new nonce each time: its ETag leaves the
            # nonce out, so a browser that has the page still gets a 304.
            content = response.content.replace(request.csp_nonce.encode(), b"")
            response["ETag"] = quote_etag(
                hashlib.md5(content, usedforsecurity=False).hexdigest()
            )
        return response
