"""Named image sizes: the renditions that templates show and that are generated when an
image is uploaded. Projects add or replace sizes with the ORION_IMAGE_SIZES setting."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from wagtail.images.models import Filter

# Every size is served in these formats, best first; the last one is the fallback.
IMAGE_FORMATS = ("avif", "webp")

IMAGE_SIZES = {
    "hero": {"filters": "fill-{800x600,1280x720,1920x1080}-c50", "sizes": "100vw"},
    "image": {
        "filters": "width-{480,800,1200,1600}",
        "sizes": "(min-width: 72rem) 70rem, 100vw",
    },
    "image_text": {
        "filters": "width-{480,800,1200}",
        "sizes": "(min-width: 48rem) 50vw, 100vw",
    },
    "gallery": {
        "filters": "fill-{400x300,800x600}",
        "sizes": "(min-width: 48rem) 33vw, 50vw",
    },
    "card": {
        "filters": "fill-{480x300,800x500}",
        "sizes": "(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw",
    },
    "carousel_card": {
        "filters": "width-{400,800}",
        "sizes": "(min-width: 48rem) 25vw, 70vw",
    },
    "logo": {"filters": "max-{240x96,480x192}", "sizes": "240px"},
    "article": {
        "filters": "width-{480,800,1200,1600}",
        "sizes": "(min-width: 56rem) 54rem, 100vw",
    },
    # The header and footer logos: 40 px tall, at double density.
    "site_logo": {"filters": "height-80", "sizes": ""},
}


def get_image_sizes():
    return {**IMAGE_SIZES, **getattr(settings, "ORION_IMAGE_SIZES", {})}


def get_image_size(name):
    try:
        return get_image_sizes()[name]
    except KeyError:
        raise ImproperlyConfigured(
            f"Unknown image size {name!r}. Add it to ORION_IMAGE_SIZES or use one of: "
            f"{', '.join(sorted(get_image_sizes()))}."
        ) from None


def size_filter_specs(name, image_format):
    """The filter specs of a size in one format, smallest first."""
    specs = Filter.expand_spec(get_image_size(name)["filters"])
    return [f"{spec}|format-{image_format}" for spec in specs]


def svg_filter_spec(name):
    """The size's largest spec, keeping the image as SVG."""
    return f"{Filter.expand_spec(get_image_size(name)['filters'])[-1]}|preserve-svg"


def all_filter_specs(image):
    """Every rendition the named sizes show for the image."""
    if image.is_svg():
        return [svg_filter_spec(name) for name in get_image_sizes()]
    return [
        spec
        for name in get_image_sizes()
        for image_format in IMAGE_FORMATS
        for spec in size_filter_specs(name, image_format)
    ]


def get_leading_hero_image(page):
    """The image of the page's first block when it is a hero, if any (not a sample
    or SVG image)."""
    body = getattr(page, "body", None)
    first = body[0] if body else None
    if first is None or first.block_type != "hero":
        return None
    return _preloadable(first.value.get("image"))


def get_leading_carousel_image(page):
    """The first image of the full-width carousel that opens the page, if any."""
    if not getattr(page, "starts_with_full_carousel", False):
        return None
    first = next(block for block in page.body if block.block_type == "carousel")
    return _preloadable(first.value["slides"][0].get("image"))


def _preloadable(image):
    if not image or getattr(image, "is_sample", False) or image.is_svg():
        return None
    return image
