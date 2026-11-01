import datetime

from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils import timezone
from wagtail.contrib.search_promotions.models import Query

from orion.editor.roles import is_site_administrator
from orion.search.models import NoResultsQuery

REPORT_DAYS = 30
REPORT_SIZE = 50


def report(request):
    """What visitors search: the most frequent searches and those without results."""
    if not is_site_administrator(request.user):
        raise PermissionDenied
    since = timezone.localdate() - datetime.timedelta(days=REPORT_DAYS)
    return TemplateResponse(
        request,
        "orion/search/admin/report.html",
        {
            "days": REPORT_DAYS,
            "popular": [
                (query.query_string, query._hits)
                for query in Query.get_most_popular(date_since=since)[:REPORT_SIZE]
            ],
            "no_results": NoResultsQuery.objects.order_by("-hits", "-last_seen")[
                :REPORT_SIZE
            ],
        },
    )
