"""Empty the page cache when anything shown on public pages changes."""

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from wagtail.models import Page
from wagtail.signals import page_published, page_unpublished, post_page_move

from orion.core.cache import clear_page_cache

# Models shown on public pages, besides pages themselves.
INVALIDATING_MODELS = [
    "orion_site_data.SiteSettings",
    "orion_site_data.SiteTexts",
    "orion_navigation.Menu",
    "orion_localization.LanguageSettings",
    "orion_pages.ArticleCategory",
    "orion_pages.ArticleTag",
    "wagtailcore.Locale",
    "wagtailcore.Site",
    "wagtailimages.Image",
    "wagtailredirects.Redirect",
]


def _clear(**kwargs):
    clear_page_cache()


def _clear_on_page_delete(sender, instance, **kwargs):
    if isinstance(instance, Page):
        clear_page_cache()


def connect():
    for signal in (page_published, page_unpublished, post_page_move):
        signal.connect(_clear, dispatch_uid=f"orion_page_cache_{signal!r}")
    post_delete.connect(_clear_on_page_delete, dispatch_uid="orion_page_cache_delete")
    labels = INVALIDATING_MODELS + list(settings.ORION_PAGE_CACHE_MODELS)
    for label in labels:
        model = apps.get_model(label)
        for signal in (post_save, post_delete):
            signal.connect(
                _clear,
                sender=model,
                dispatch_uid=f"orion_page_cache_{label}_{signal!r}",
            )
