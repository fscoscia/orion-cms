from django import template
from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils.translation import get_language

from orion.core.cache import generation_key
from orion.navigation.models import Menu, MenuLocation

register = template.Library()


def _link_data(link):
    """A link as plain data that can be cached: what link.html needs, plus the tree
    path of its page to mark the current item."""
    page = link.linked_page
    return {
        "href": link.href,
        "text": link.text,
        "opens_in_new_tab": link.opens_in_new_tab,
        "is_visible": link.is_visible,
        # A link to a section does not stand for its page: on a landing, every item
        # would be marked.
        "page_path": page.path if page is not None and not link.get("anchor") else None,
    }


def _resolve_items(menu):
    """The menu's visible items with their visible subitems, as plain data.

    An item without a destination is kept as a group title only while it has at least
    one visible subitem.
    """
    items = []
    for block in menu.items:
        link = block.value["link"]
        subitems = [
            {"link": _link_data(subitem)}
            for subitem in block.value["subitems"]
            if subitem.is_visible
        ]
        if not link.is_visible and not subitems:
            continue
        items.append(
            {"link": _link_data(link), "text": link.text, "subitems": subitems}
        )
    return items


def _get_items(location, request):
    """The resolved items of the location's menu, computed once per language and
    site until the page cache empties."""
    host = request.get_host() if request is not None else ""
    key = generation_key("menu", location, get_language(), host)
    items = cache.get(key)
    if items is None:
        menu = Menu.for_active_language(location)
        items = _resolve_items(menu) if menu is not None else []
        cache.set(key, items, settings.ORION_PAGE_CACHE_SECONDS)
    return items


def _is_current(link, current_page):
    """Whether the link points to the current page or one of its ancestors."""
    page_path = link["page_path"]
    return bool(page_path and current_page) and current_page.path.startswith(page_path)


def _mark_current(items, current_page):
    marked = []
    for item in items:
        subitems = [
            {**subitem, "is_current": _is_current(subitem["link"], current_page)}
            for subitem in item["subitems"]
        ]
        is_current = _is_current(item["link"], current_page) or any(
            subitem["is_current"] for subitem in subitems
        )
        marked.append({**item, "subitems": subitems, "is_current": is_current})
    return marked


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
    items = _mark_current(
        _get_items(location, context.get("request")), context.get("page")
    )
    if not items:
        return ""
    return render_to_string(
        f"orion/includes/menu_{location}.html",
        {"items": items, "location": location},
        request=context.get("request"),
    )
