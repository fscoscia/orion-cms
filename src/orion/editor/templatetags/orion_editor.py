from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from wagtail.models import Site

from orion.core.csp import add_nonce

register = template.Library()


@register.simple_tag
def admin_site_name():
    """The site name for the admin: the default site's, or WAGTAIL_SITE_NAME."""
    site = Site.objects.filter(is_default_site=True).first()
    return (site.site_name if site else "") or getattr(
        settings, "WAGTAIL_SITE_NAME", ""
    )


@register.simple_tag
def admin_logo(kind="logo"):
    """The site's logo (``logo``) or its light version (``footer_logo``), or None."""
    # Imported here: settings models load after template tag libraries are found.
    from orion.site_data.models import SiteSettings

    return getattr(SiteSettings.load(), kind)


@register.filter
def in_minutes(duration):
    """A timedelta as whole minutes, rounded up."""
    return -(-int(duration.total_seconds()) // 60)


@register.filter
def with_nonce(html, nonce):
    """Wagtail's own script tags with the content security policy's nonce."""
    return mark_safe(add_nonce(str(html), nonce))  # noqa: S308 - Wagtail's markup
