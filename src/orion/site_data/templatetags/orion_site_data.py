from django import template

from orion.site_data.models import SOCIAL_NETWORK_CHOICES, SiteTexts

register = template.Library()


@register.simple_tag
def get_site_texts():
    """Return the site texts for the active language, falling back to the base one."""
    return SiteTexts.for_active_language()


@register.filter
def social_network_name(network):
    """Return the display name of a social network key, such as "LinkedIn"."""
    return dict(SOCIAL_NETWORK_CHOICES).get(network, network)
