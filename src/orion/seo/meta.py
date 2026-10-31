"""The metadata a page gives search engines and social networks."""

import json

from django.conf import settings
from django.utils.translation import get_language, to_locale
from wagtail.models import Site

from orion.site_data.models import SiteSettings, SiteTexts

SOCIAL_IMAGE_FILTER = "fill-1200x630|format-jpeg"
FAVICON_SIZES = (32, 192)
APPLE_TOUCH_ICON_SIZE = 180
ORGANIZATION_LOGO_FILTER = "max-512x512|format-png"

# The characters that could close a <script> element, as in Django's json_script.
JSON_SCRIPT_ESCAPES = {ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"}


def get_site(request):
    return (
        Site.find_for_request(request)
        or Site.objects.filter(is_default_site=True).first()
    )


def get_site_name(site):
    return (site.site_name if site else "") or settings.WAGTAIL_SITE_NAME


def get_title(page, site_name):
    if page is None:
        return site_name
    if page.seo_title:
        return page.seo_title
    if page.title == site_name:
        return page.title
    return f"{page.title} | {site_name}"


def get_canonical_url(request, page, site, listing=None):
    """The page's absolute URL, built for this visit: no query string except the
    number of a listing page after the first."""
    if page is None:
        return request.build_absolute_uri(request.path)
    page_url = page.get_url(request)
    if site and page_url and request.path != page_url:
        # A route of a routable page, such as a category of a listing.
        url = f"{site.root_url}{request.path}"
    else:
        url = page.get_full_url(request)
    number = getattr(listing, "number", 1)
    return f"{url}?page={number}" if number > 1 else url


def absolute_url(request, url):
    return request.build_absolute_uri(url)


def image_url(request, image, filter_spec):
    if image is None:
        return None
    if image.is_svg():
        return None
    return absolute_url(request, image.get_rendition(filter_spec).url)


def get_social_image(page, site_settings):
    image = page.get_social_image() if hasattr(page, "get_social_image") else None
    image = image or site_settings.social_image
    return None if image is None or image.is_svg() else image


def get_favicons(request, image):
    """``(rel, type, sizes, url)`` of the favicon links."""
    if image is None:
        return []
    if image.is_svg():
        url = image.get_rendition("original|preserve-svg").url
        return [("icon", "image/svg+xml", "any", absolute_url(request, url))]
    icons = [
        (
            "icon",
            "image/png",
            f"{size}x{size}",
            image_url(request, image, f"fill-{size}x{size}|format-png"),
        )
        for size in FAVICON_SIZES
    ]
    size = APPLE_TOUCH_ICON_SIZE
    icons.append(
        (
            "apple-touch-icon",
            "",
            f"{size}x{size}",
            image_url(request, image, f"fill-{size}x{size}|format-png"),
        )
    )
    return icons


def get_seo_context(request, page=None, listing=None):
    site = get_site(request)
    site_name = get_site_name(site)
    site_settings = SiteSettings.load(request_or_site=request)
    texts = SiteTexts.for_active_language()
    page_description = ""
    if page is not None:
        page_description = (
            page.get_meta_description()
            if hasattr(page, "get_meta_description")
            else page.search_description
        )
    description = page_description or (texts.description if texts else "")
    social_image = get_social_image(page, site_settings)
    return {
        "title": get_title(page, site_name),
        "og_title": (page.seo_title or page.title) if page else site_name,
        "description": description,
        "canonical_url": get_canonical_url(request, page, site, listing),
        "robots": ", ".join(
            directive
            for directive, is_on in (
                ("noindex", getattr(page, "no_index", False)),
                ("nofollow", getattr(page, "no_follow", False)),
            )
            if is_on
        ),
        "site_name": site_name,
        "og_type": getattr(page, "og_type", "website"),
        "og_locale": to_locale(get_language() or settings.LANGUAGE_CODE),
        "social_image_url": image_url(request, social_image, SOCIAL_IMAGE_FILTER),
        "google_site_verification": site_settings.google_site_verification,
        "favicons": get_favicons(request, site_settings.favicon),
    }


def _breadcrumbs(request, page, site):
    root_depth = site.root_page.depth if site else 2
    if page is None or page.depth <= root_depth:
        return None
    ancestors = page.get_ancestors(inclusive=True).filter(depth__gte=root_depth)
    items = [
        {
            "@type": "ListItem",
            "position": position,
            "name": ancestor.title,
            "item": ancestor.get_full_url(request),
        }
        for position, ancestor in enumerate(ancestors.live().specific(), start=1)
    ]
    return {"@type": "BreadcrumbList", "itemListElement": items}


def _organization(request, site_settings, site_name, home_url):
    logo = site_settings.logo
    organization = {
        "@type": "Organization",
        "@id": f"{home_url}#organization",
        "name": site_name,
        "url": home_url,
        "logo": image_url(request, logo, ORGANIZATION_LOGO_FILTER)
        or (
            absolute_url(request, logo.get_rendition("original|preserve-svg").url)
            if logo
            else None
        ),
        "telephone": site_settings.phone,
        "email": site_settings.email,
        "address": site_settings.address,
        "sameAs": [link.value["url"] for link in site_settings.social_links],
    }
    return {key: value for key, value in organization.items() if value}


def _iso(value):
    return value.isoformat() if value else None


def get_structured_data(request, page=None):
    """The JSON-LD graph of the page, as a string safe inside <script>."""
    site = get_site(request)
    site_name = get_site_name(site)
    site_settings = SiteSettings.load(request_or_site=request)
    home_url = (site.root_url if site else request.build_absolute_uri("/")).rstrip(
        "/"
    ) + "/"
    language = get_language() or settings.LANGUAGE_CODE
    graph = [
        {
            "@type": "WebSite",
            "@id": f"{home_url}#website",
            "name": site_name,
            "url": home_url,
            "inLanguage": language,
        },
        _organization(request, site_settings, site_name, home_url),
    ]
    breadcrumbs = _breadcrumbs(request, page, site)
    if breadcrumbs:
        graph.append(breadcrumbs)
    if getattr(page, "og_type", "") == "article":
        article = {
            "@type": "Article",
            "headline": page.title,
            "description": page.search_description or getattr(page, "summary", ""),
            "image": image_url(
                request, get_social_image(page, site_settings), SOCIAL_IMAGE_FILTER
            ),
            "datePublished": _iso(
                getattr(page, "date", None) or page.first_published_at
            ),
            "dateModified": _iso(page.last_published_at),
            "inLanguage": language,
            "mainEntityOfPage": page.get_full_url(request),
            "publisher": {"@id": f"{home_url}#organization"},
        }
        graph.append({key: value for key, value in article.items() if value})
    data = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(data, ensure_ascii=False).translate(JSON_SCRIPT_ESCAPES)
