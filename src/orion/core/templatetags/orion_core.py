from django import template

from orion.core.blocks import normalize_phone

register = template.Library()


@register.filter
def tel_url(phone):
    """Turn a phone as typed by an editor into a ``tel:`` URL."""
    return f"tel:{normalize_phone(phone)}" if phone else ""


@register.filter
def whatsapp_url(phone):
    """Turn a phone as typed by an editor into a WhatsApp chat URL."""
    return f"https://wa.me/{normalize_phone(phone).lstrip('+')}" if phone else ""
