from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.cache import get_conditional_response
from django.utils.http import http_date, parse_http_date_safe

from orion.core.cache import generation_key
from orion.core.csp import new_nonce

# Headers that belong to one visitor or to this cache, never stored.
SKIPPED_HEADERS = {"set-cookie", "x-orion-cache"}
UNCACHEABLE_DIRECTIVES = ("private", "no-store", "no-cache")


class PageCacheMiddleware:
    """Serve repeated visits of visitors without a session from the cache."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._is_cacheable_request(request):
            return self.get_response(request)
        key = generation_key("page", request.get_host(), request.get_full_path())
        cached = cache.get(key)
        if cached is not None:
            return self._from_cache(request, cached)
        response = self.get_response(request)
        if request.method == "GET" and self._is_cacheable_response(request, response):
            if not response.has_header("Last-Modified"):
                response["Last-Modified"] = http_date()
            cache.set(
                key,
                {
                    "content": response.content,
                    "nonce": getattr(request, "csp_nonce", ""),
                    "headers": [
                        (name, value)
                        for name, value in response.items()
                        if name.lower() not in SKIPPED_HEADERS
                    ],
                },
                settings.ORION_PAGE_CACHE_SECONDS,
            )
            response["X-Orion-Cache"] = "miss"
        return response

    @staticmethod
    def _is_cacheable_request(request):
        if not settings.ORION_PAGE_CACHE or request.method not in ("GET", "HEAD"):
            return False
        # Wagtail's previews render through a dummy request with the page's path.
        if getattr(request, "is_dummy", False) or getattr(request, "is_preview", False):
            return False
        if settings.SESSION_COOKIE_NAME in request.COOKIES:
            return False
        excluded = (
            f"/{settings.ORION_ADMIN_PATH}",
            settings.STATIC_URL,
            settings.MEDIA_URL,
            "/_preview/",
        )
        return not request.path.startswith(
            tuple("/" + prefix.lstrip("/") for prefix in excluded if prefix)
        )

    @staticmethod
    def _is_cacheable_response(request, response):
        if response.status_code != 200 or response.streaming or response.cookies:
            return False
        if getattr(request, "is_preview", False):
            return False
        # A page with a CSRF token belongs to one visitor. Every page varies on the
        # cookie (Wagtail's user bar reads the session), so that header says nothing:
        # entries are only served to visitors without a session cookie.
        if request.META.get("CSRF_COOKIE_NEEDS_UPDATE"):
            return False
        cache_control = response.get("Cache-Control", "").lower()
        return not any(
            directive in cache_control for directive in UNCACHEABLE_DIRECTIVES
        )

    @staticmethod
    def _from_cache(request, cached):
        content, headers = cached["content"], cached["headers"]
        old_nonce = cached.get("nonce")
        if old_nonce:
            # Never the same nonce twice: a fresh one in the page and in its policy.
            nonce = new_nonce()
            content = content.replace(old_nonce.encode(), nonce.encode())
            headers = [
                (name, value.replace(old_nonce, nonce)) for name, value in headers
            ]
        response = HttpResponse(content)
        for name, value in headers:
            response[name] = value
        response["X-Orion-Cache"] = "hit"
        conditional = get_conditional_response(
            request,
            etag=response.get("ETag"),
            last_modified=parse_http_date_safe(response.get("Last-Modified", "")),
            response=response,
        )
        return conditional
