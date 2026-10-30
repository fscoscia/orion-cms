from django import template
from django.utils import translation
from django.utils.html import format_html, format_html_join
from wagtail.models import Locale, Page

from orion.localization.languages import (
    get_language_home_url,
    get_live_translation,
    get_public_locales,
)

register = template.Library()


@register.inclusion_tag("orion/includes/language_switcher.html", takes_context=True)
def language_switcher(context):
    """Link to the current page in every public language.

    Falls back to the language's home page when the page has no published
    translation. Renders nothing while the site has a single public language.
    """
    request = context.get("request")
    page = context.get("page")
    public_locales = get_public_locales(request)
    if len(public_locales) < 2:
        return {"languages": []}

    current_language_code = translation.get_language()
    languages = []
    for locale in public_locales:
        url = None
        if isinstance(page, Page):
            translated_page = get_live_translation(page, locale)
            if translated_page is not None:
                url = translated_page.get_url(request)
        if url is None:
            url = get_language_home_url(locale.language_code, request) or "/"
        languages.append(
            {
                "code": locale.language_code,
                "name": locale.get_display_name(),
                "url": url,
                "is_current": locale.language_code == current_language_code,
            }
        )
    return {"languages": languages}


@register.simple_tag(takes_context=True)
def hreflang_links(context):
    """Declare the page's published translations in public languages to search engines.

    Adds an ``x-default`` entry for the base-language version. Renders nothing when the
    page exists in a single public language.
    """
    request = context.get("request")
    page = context.get("page")
    if not isinstance(page, Page):
        return ""

    versions = []
    for locale in get_public_locales(request):
        translated_page = get_live_translation(page, locale)
        if translated_page is not None:
            versions.append((locale, translated_page.get_full_url(request)))
    if len(versions) < 2:
        return ""

    links = format_html_join(
        "\n",
        '<link rel="alternate" hreflang="{}" href="{}">',
        ((locale.language_code, url) for locale, url in versions),
    )
    base_locale = Locale.get_default()
    default_url = next(
        (url for locale, url in versions if locale.pk == base_locale.pk), None
    )
    if default_url is None:
        return links
    return format_html(
        '{}\n<link rel="alternate" hreflang="x-default" href="{}">',
        links,
        default_url,
    )
