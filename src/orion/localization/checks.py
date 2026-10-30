"""System checks for language settings and per-language URLs."""

from django.conf import settings
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.core.checks import Error, Tags, register
from wagtail.coreutils import get_supported_content_language_variant

BASE_LANGUAGE_NOT_IN_CATALOG_ERROR_ID = "orion.E002"
MISSING_LANGUAGE_URLS_ERROR_ID = "orion.E003"


@register(Tags.compatibility)
def check_base_language_in_catalog(app_configs, **kwargs):
    """Report a base language that the language catalog does not offer."""
    try:
        get_supported_content_language_variant(settings.LANGUAGE_CODE)
    except LookupError:
        catalog = ", ".join(code for code, _name in settings.WAGTAIL_CONTENT_LANGUAGES)
        return [
            Error(
                f"LANGUAGE_CODE {settings.LANGUAGE_CODE!r} is not in the language "
                "catalog.",
                hint=(
                    f"Use one of the catalog languages ({catalog}), or add it to both "
                    "LANGUAGES and WAGTAIL_CONTENT_LANGUAGES."
                ),
                id=BASE_LANGUAGE_NOT_IN_CATALOG_ERROR_ID,
            )
        ]
    return []


@register(Tags.urls)
def check_language_urls(app_configs, **kwargs):
    """Report a root URLconf without per-language routes at its top level.

    That happens when a project includes ``orion.urls`` with ``include()`` instead of
    adding its routes, which Django requires for per-language URLs.
    """
    is_used, _prefixes_default_language = is_language_prefix_patterns_used(
        settings.ROOT_URLCONF
    )
    if is_used:
        return []
    return [
        Error(
            "The root URLconf has no per-language routes.",
            hint=(
                "Add Orion's routes to the project's URLconf instead of including "
                "them: 'from orion.urls import urlpatterns as orion_urlpatterns' and "
                "'urlpatterns += orion_urlpatterns'."
            ),
            id=MISSING_LANGUAGE_URLS_ERROR_ID,
        )
    ]
