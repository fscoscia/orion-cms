from django.shortcuts import redirect
from django.utils import translation
from wagtail import hooks

from orion.localization.languages import get_language_home_url


@hooks.register("before_serve_page")
def redirect_pages_served_in_another_language(page, request, serve_args, kwargs):
    """Redirect when Wagtail serves a page whose language differs from the URL's.

    Wagtail resolves prefixed URLs from the root page's translation in the active
    language and falls back to the base language's tree when that translation is
    missing, which would show base-language content under a secondary prefix.
    """
    requested_language_code = translation.get_language()
    if page.locale.language_code == requested_language_code:
        return None
    home_url = get_language_home_url(requested_language_code, request) or "/"
    if home_url == request.path:
        home_url = "/"
    return redirect(home_url)
