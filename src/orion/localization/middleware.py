from django.conf import settings
from django.shortcuts import redirect
from django.utils import translation

from orion.localization.languages import (
    get_language_home_url,
    get_public_language_codes,
)

SAFE_METHODS = frozenset({"GET", "HEAD"})


class LocaleRedirectMiddleware:
    """Redirect visitors away from languages they cannot see or pages that are missing.

    Only URLs with the prefix of a secondary language are affected: unprefixed URLs
    belong to the base language and keep their normal behaviour, including 404 pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language_code = self._get_secondary_language_from_path(request)
        if language_code is None or request.method not in SAFE_METHODS:
            return self.get_response(request)

        if language_code not in get_public_language_codes(request):
            return redirect("/")

        response = self.get_response(request)
        if response.status_code == 404:
            home_url = get_language_home_url(language_code, request) or "/"
            if home_url != request.path:
                return redirect(home_url)
            if request.path != "/":
                return redirect("/")
        return response

    @staticmethod
    def _get_secondary_language_from_path(request):
        language_code = translation.get_language_from_path(request.path_info)
        if language_code is None:
            return None
        base_language_code = translation.get_supported_language_variant(
            settings.LANGUAGE_CODE
        )
        if language_code == base_language_code:
            return None
        return language_code
