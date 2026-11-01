from django import template
from django.conf import settings
from django.core.cache import cache
from django.utils.safestring import mark_safe
from wagtail.models import Locale

from orion.core.cache import generation_key
from orion.snippets.models import CodeSnippet, Scope

register = template.Library()


def _active_snippets():
    """The active snippets as plain data, read once until the page cache empties."""
    key = generation_key("code-snippets")
    snippets = cache.get(key)
    if snippets is None:
        snippets = [
            {
                "location": snippet.location,
                "code": snippet.code,
                "scope": snippet.scope,
                "page_paths": [item.page.path for item in snippet.snippet_pages.all()],
                "include_subpages": snippet.include_subpages,
                "page_type_ids": [
                    content_type.pk for content_type in snippet.page_types.all()
                ],
                "locale_ids": [locale.pk for locale in snippet.locales.all()],
            }
            for snippet in CodeSnippet.objects.filter(is_active=True).prefetch_related(
                "snippet_pages__page", "page_types", "locales"
            )
        ]
        cache.set(key, snippets, settings.ORION_PAGE_CACHE_SECONDS)
    return snippets


def _applies(snippet, page, locale_id):
    if snippet["locale_ids"] and locale_id not in snippet["locale_ids"]:
        return False
    if snippet["scope"] == Scope.SITE:
        return True
    if page is None:
        return False
    if snippet["scope"] == Scope.PAGE_TYPES:
        return page.content_type_id in snippet["page_type_ids"]
    return any(
        page.path == path
        or (snippet["include_subpages"] and page.path.startswith(path))
        for path in snippet["page_paths"]
    )


@register.simple_tag(takes_context=True)
def code_snippets(context, location):
    """The active code snippets of a location ("head", "body_start" or "body_end")
    for the current page. Never in previews; ORION_SCRIPTS_DISABLED turns them off."""
    request = context.get("request")
    if settings.ORION_SCRIPTS_DISABLED or request is None:
        return ""
    if getattr(request, "is_preview", False):
        return ""
    page = context.get("page") or None
    snippets = [
        snippet for snippet in _active_snippets() if snippet["location"] == location
    ]
    if not snippets:
        return ""
    locale_id = Locale.get_active().pk
    # Pasted by people with the dedicated permission: trusted code, inserted as is.
    return mark_safe(  # noqa: S308
        "\n".join(
            snippet["code"]
            for snippet in snippets
            if _applies(snippet, page, locale_id)
        )
    )
