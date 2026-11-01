"""The site's search results page."""

from django.conf import settings
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.db.models import F
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.search_promotions.models import Query
from wagtail.models import Locale, Page
from wagtail.search.query import Fuzzy
from wagtail.search.utils import normalise_query_string

from orion.search.backend import has_trigram
from orion.search.models import NoResultsQuery
from orion.seo.models import get_not_indexed_ids

# The results page's address, translated: "buscar/" in Spanish.
SEARCH_PATH = _("search/")
RESULTS_PER_PAGE = 10
MAX_QUERY_LENGTH = 100
TYPE_CHOICES = [("page", _("Pages")), ("article", _("Articles"))]


def _searchable_pages(page_type):
    # Imported here: the pages app loads after this one.
    from orion.pages.models import ArticlePage

    pages = (
        Page.objects.live()
        .public()
        .filter(locale=Locale.get_active(), depth__gt=1)
        .exclude(pk__in=get_not_indexed_ids())
    )
    if page_type == "article":
        return pages.type(ArticlePage)
    if page_type == "page":
        return pages.not_type(ArticlePage)
    return pages


def _promoted(query):
    """Promoted pages for the query, published and in the visitor's language."""
    try:
        promotions = Query.objects.get(
            query_string=normalise_query_string(query)
        ).editors_picks
    except Query.DoesNotExist:
        return []
    return [
        (promotion.page.localized.specific, promotion.description)
        for promotion in promotions.select_related("page").order_by("sort_order")
        if promotion.page and promotion.page.localized.live
    ]


def _record(query, found):
    Query.get(query).add_hit()
    if found:
        return
    normalised = normalise_query_string(query)[
        : NoResultsQuery._meta.get_field("query_string").max_length
    ]
    if NoResultsQuery.objects.filter(query_string=normalised).update(
        hits=F("hits") + 1
    ):
        return
    if NoResultsQuery.objects.count() < settings.ORION_SEARCH_MAX_NO_RESULTS:
        NoResultsQuery.objects.get_or_create(query_string=normalised)


def _result(page, description=""):
    page = page.specific
    summary = description or (
        page.get_meta_description()
        if hasattr(page, "get_meta_description")
        else page.search_description
    )
    return {
        "page": page,
        "url": page.url,
        "title": page.title,
        "summary": summary,
        "type": page.specific_class._meta.verbose_name,
    }


def search(request):
    query = request.GET.get("q", "").strip()[:MAX_QUERY_LENGTH]
    page_type = request.GET.get("type", "")
    if page_type not in dict(TYPE_CHOICES):
        page_type = ""
    context = {"query": query, "page_type": page_type, "type_choices": TYPE_CHOICES}
    if query:
        pages = _searchable_pages(page_type)
        results = pages.search(query, operator="and", order_by_relevance=True)
        if not results.count() and has_trigram():
            # Approximate search tolerates typos; a failure must not break the page.
            try:
                with transaction.atomic():
                    results = pages.search(Fuzzy(query))
                    results.count()
            except DatabaseError:
                results = pages.search(query, operator="and")
        promoted = _promoted(query) if request.GET.get("page", "1") == "1" else []
        promoted_ids = {page.pk for page, _description in promoted}
        paginator = Paginator(results, RESULTS_PER_PAGE)
        current = paginator.get_page(request.GET.get("page"))
        context.update(
            promoted=[_result(page, description) for page, description in promoted],
            results=[
                _result(page)
                for page in current.object_list
                if page.pk not in promoted_ids
            ],
            results_page=current,
            total=paginator.count,
        )
        if current.number == 1:
            _record(query, paginator.count or promoted)
    return TemplateResponse(request, "orion/search/search.html", context)
