from django import template
from django.template.loader import render_to_string

from orion.navigation.models import Menu, MenuLocation

register = template.Library()


def _build_items(menu, current_page):
    """Return the menu's visible items with their visible subitems.

    An item without a destination is kept as a group title only while it has at least
    one visible subitem.
    """
    items = []
    for block in menu.items:
        link = block.value["link"]
        subitems = [
            {"link": subitem, "is_current": subitem.has_page(current_page)}
            for subitem in block.value["subitems"]
            if subitem.is_visible
        ]
        if not link.is_visible and not subitems:
            continue
        is_current = link.has_page(current_page) or any(
            subitem["is_current"] for subitem in subitems
        )
        items.append(
            {
                "link": link,
                "text": link.text,
                "is_current": is_current,
                "subitems": subitems,
            }
        )
    return items


@register.simple_tag(takes_context=True)
def site_menu(context, location):
    """Render the menu for ``location`` in the active language.

    Uses ``orion/includes/menu_<location>.html``, which projects can override.
    Renders nothing when the location has no menu or no visible items.
    """
    if location not in MenuLocation.values:
        raise template.TemplateSyntaxError(
            f"Unknown menu location {location!r}; use one of {MenuLocation.values}."
        )
    menu = Menu.for_active_language(location)
    if menu is None:
        return ""
    items = _build_items(menu, context.get("page"))
    if not items:
        return ""
    return render_to_string(
        f"orion/includes/menu_{location}.html",
        {"items": items, "location": location},
        request=context.get("request"),
    )
