from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.decorators.cache import cache_control

from orion.editor.colors import admin_colors_css
from orion.editor.home import get_article_listings


@cache_control(max_age=3600, public=True)
def admin_colors(request):
    """The admin color variables from ORION_ADMIN_COLORS.

    Served outside Wagtail's admin URLs because the login page needs it too; it only
    exposes colors from the settings.
    """
    return HttpResponse(admin_colors_css(), content_type="text/css; charset=utf-8")


def new_article(request):
    """Start an article in the only listing, or let the editor choose the listing."""
    listings = get_article_listings(request.user)
    if not listings:
        raise Http404
    if len(listings) == 1:
        return redirect(
            "wagtailadmin_pages:add", "orion_pages", "articlepage", listings[0].pk
        )
    return TemplateResponse(
        request, "orion/editor/new_article.html", {"listings": listings}
    )
