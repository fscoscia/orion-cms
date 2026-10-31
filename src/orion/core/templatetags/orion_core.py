import re
from urllib.parse import urlencode

from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from wagtail.images.models import Picture
from wagtail.rich_text import expand_db_html

from orion.core.blocks import normalize_phone
from orion.core.images import (
    IMAGE_FORMATS,
    get_image_size,
    get_leading_hero_image,
    size_filter_specs,
    svg_filter_spec,
)

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


def _size_renditions(image, size):
    specs = [
        spec
        for image_format in IMAGE_FORMATS
        for spec in size_filter_specs(size, image_format)
    ]
    return image.get_renditions(*specs)


@register.simple_tag
def responsive_image(
    image, size, alt="", class_name="", is_main=False, is_lazy=True, **attrs
):
    """Show an image at a named size (see orion.core.images): a <picture> with AVIF and
    WebP sources, with its width and height.

    The page's main image (``is_main``) is fetched first; images above the fold that are
    not the main one pass ``is_lazy=False``.
    """
    if not image:
        return ""
    if getattr(image, "is_sample", False):
        return render_to_string(
            "orion/blocks/includes/sample_image.html",
            {"image": image, "alt": alt, "class_name": class_name},
        )
    attrs = {"alt": alt, "class": class_name or None, **attrs}
    if is_main:
        attrs["fetchpriority"] = "high"
    elif is_lazy:
        attrs.update(loading="lazy", decoding="async")
    if image.is_svg():
        return image.get_rendition(svg_filter_spec(size)).img_tag(attrs)
    attrs["sizes"] = get_image_size(size)["sizes"] or None
    return Picture(_size_renditions(image, size), attrs).__html__()


@register.simple_tag
def main_image_preload(page):
    """Preload the hero image of a page that starts with one, for <head>."""
    image = get_leading_hero_image(page) if page else None
    if image is None:
        return ""
    renditions = image.get_renditions(*size_filter_specs("hero", IMAGE_FORMATS[0]))
    srcset = ", ".join(
        f"{rendition.url} {rendition.width}w" for rendition in renditions.values()
    )
    return format_html(
        '<link rel="preload" as="image" type="image/{}" imagesrcset="{}" '
        'imagesizes="{}" fetchpriority="high">',
        IMAGE_FORMATS[0],
        srcset,
        get_image_size("hero")["sizes"],
    )


@register.simple_tag
def font_preloads():
    """Preload the project's fonts listed in ORION_FONT_PRELOAD, for <head>."""
    return format_html_join(
        "",
        '<link rel="preload" href="{}" as="font" type="font/woff2" crossorigin>',
        ((static(path),) for path in settings.ORION_FONT_PRELOAD),
    )
