from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from orion.seo.meta import get_seo_context, get_structured_data

register = template.Library()


@register.simple_tag(takes_context=True)
def seo_tags(context, page=None):
    """Title, description, canonical URL, robots, social network and favicon tags."""
    request = context["request"]
    # A listing's paginated articles, to keep ?page=N in the canonical URL.
    listing = context.get("articles")
    return render_to_string(
        "orion/seo/head.html",
        get_seo_context(request, page, listing),
        request=request,
    )


@register.simple_tag(takes_context=True)
def structured_data(context, page=None):
    """The page's JSON-LD (site, organization, breadcrumbs and article)."""
    data = get_structured_data(context["request"], page)
    # Safe: get_structured_data escapes the characters that could close the tag.
    return mark_safe(f'<script type="application/ld+json">{data}</script>')  # noqa: S308
