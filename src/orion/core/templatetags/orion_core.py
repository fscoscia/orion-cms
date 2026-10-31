import re
from urllib.parse import urlencode

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from wagtail.rich_text import expand_db_html

from orion.core.blocks import normalize_phone

register = template.Library()

PARAGRAPH_TAGS = re.compile(r"</?p\b[^>]*>")


@register.filter
def tel_url(phone):
    """Turn a phone as typed by an editor into a ``tel:`` URL."""
    return f"tel:{normalize_phone(phone)}" if phone else ""


@register.filter
def whatsapp_url(phone):
    """Turn a phone as typed by an editor into a WhatsApp chat URL."""
    return f"https://wa.me/{normalize_phone(phone).lstrip('+')}" if phone else ""


@register.filter
def highlighted_title(title):
    """Render a highlighted title's rich text without its paragraph, for a heading."""
    if not title:
        return ""
    html = expand_db_html(getattr(title, "source", str(title)))
    # Safe: Wagtail stores rich text already filtered to the block's allowed features.
    return mark_safe(PARAGRAPH_TAGS.sub("", html).strip())  # noqa: S308


@register.filter
def visible_links(links):
    """Return the links that have a destination the visitor can reach."""
    return [link for link in links or () if link.is_visible]


@register.simple_tag
def get_map_tiles():
    """Return the tile provider settings for maps (ORION_MAP_TILES)."""
    return settings.ORION_MAP_TILES


@register.filter
def openstreetmap_url(point, zoom=16):
    """Return a link that opens a map point on openstreetmap.org."""
    query = urlencode({"mlat": point["lat"], "mlon": point["lng"]})
    return f"https://www.openstreetmap.org/?{query}#map={zoom}/{point['lat']}/{point['lng']}"
