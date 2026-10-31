import datetime

from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.decorators.cache import cache_control

from orion.editor import scheduling
from orion.editor.colors import admin_colors_css
from orion.editor.home import get_article_listings
from orion.editor.roles import is_site_administrator


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


def _month(value, today):
    """The first day of the month in ``value`` (YYYY-MM), or of today's month."""
    try:
        month = datetime.datetime.strptime(value or "", "%Y-%m").date()
    except ValueError:
        return today.replace(day=1)
    # Far years would overflow the previous and next month links.
    return month if 1900 <= month.year <= 9000 else today.replace(day=1)


def publication_calendar(request):
    """The month's scheduled publications and expiries of pages the user can edit."""
    today = timezone.localdate()
    month = _month(request.GET.get("month"), today)
    previous_month = (month - datetime.timedelta(days=1)).replace(day=1)
    next_month = (month + datetime.timedelta(days=31)).replace(day=1)
    entries = scheduling.month_entries(request.user, month.year, month.month)
    weeks = [
        [{"date": day, "entries": entries.get(day, [])} for day in week]
        for week in scheduling.month_weeks(month.year, month.month)
    ]
    return TemplateResponse(
        request,
        "orion/editor/calendar.html",
        {
            "month": month,
            "today": today,
            "weeks": weeks,
            "days_with_entries": sorted(entries.items()),
            # The second week is always whole: it names the columns.
            "weekdays": [day["date"] for day in weeks[1]],
            "previous_month": previous_month.strftime("%Y-%m"),
            "next_month": next_month.strftime("%Y-%m"),
            "is_current_month": month == today.replace(day=1),
            "overdue_count": scheduling.overdue_count()
            if is_site_administrator(request.user)
            else 0,
        },
    )
