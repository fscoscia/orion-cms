"""Queries about the site's languages shared by the middleware, hooks and templates."""

from django.http import HttpRequest
from wagtail.models import Locale, Page, Site

from orion.localization.models import LanguageSettings

_PUBLIC_LOCALES_CACHE_ATTRIBUTE = "_orion_public_locales"


def get_public_locales(request: HttpRequest | None = None) -> list[Locale]:
    """Return the locales visitors can see, always including the base language.

    The result is cached on the request because the middleware, the page hook and the
    templates all ask for it while serving the same page.
    """
    if request is not None and hasattr(request, _PUBLIC_LOCALES_CACHE_ATTRIBUTE):
        return getattr(request, _PUBLIC_LOCALES_CACHE_ATTRIBUTE)

    language_settings = LanguageSettings.load(request_or_site=request)
    public_locale_ids = set(
        language_settings.public_locales.values_list("pk", flat=True)
    )
    public_locale_ids.add(Locale.get_default().pk)
    public_locales = list(
        Locale.objects.filter(pk__in=public_locale_ids).order_by("language_code")
    )

    if request is not None:
        setattr(request, _PUBLIC_LOCALES_CACHE_ATTRIBUTE, public_locales)
    return public_locales


def get_public_language_codes(request: HttpRequest | None = None) -> set[str]:
    """Return the language codes of the locales visitors can see."""
    return {locale.language_code for locale in get_public_locales(request)}


def get_language_home_url(language_code: str, request: HttpRequest) -> str | None:
    """Return the URL of the site's published home page in a language, if any."""
    site = Site.find_for_request(request)
    if site is None:
        return None
    locale = Locale.objects.filter(language_code=language_code).first()
    if locale is None:
        return None
    home_page = site.root_page.get_translation_or_none(locale)
    if home_page is None or not home_page.live:
        return None
    return home_page.get_url(request)


def get_live_translation(page: Page, locale: Locale) -> Page | None:
    """Return the published version of ``page`` in ``locale``, if it exists."""
    if page.locale_id == locale.pk:
        return page if page.live else None
    translation = page.get_translation_or_none(locale)
    if translation is None or not translation.live:
        return None
    return translation
