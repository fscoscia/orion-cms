from wagtail.contrib.sitemaps import Sitemap as WagtailSitemap
from wagtail.models import Page

from orion.localization.languages import get_public_locales
from orion.seo.models import get_not_indexed_ids


class Sitemap(WagtailSitemap):
    """Wagtail's sitemap, with the pages of every public language and without the
    pages marked not to be indexed."""

    def items(self):
        root = self.get_wagtail_site().root_page
        roots = [
            root
            if root.locale_id == locale.pk
            else root.get_translation_or_none(locale)
            for locale in get_public_locales(self.request)
        ]
        pages = Page.objects.none()
        for translated_root in filter(None, roots):
            pages |= Page.objects.descendant_of(translated_root, inclusive=True)
        # Wagtail's sitemap iterates a queryset, so pages are excluded by id.
        return (
            pages.exclude(pk__in=get_not_indexed_ids())
            .live()
            .public()
            .order_by("path")
            .defer_streamfields()
            .specific()
        )
