import pytest
from django.core.cache import cache
from django.urls import set_script_prefix
from wagtail.models import Locale, Page, Site

from orion.localization.models import LanguageSettings


@pytest.fixture
def url_prefix():
    """Serve a test's requests under /sub, as a deployment in a subfolder does."""
    set_script_prefix("/sub/")
    yield {"SCRIPT_NAME": "/sub"}
    set_script_prefix("/")


@pytest.fixture
def home_page(db):
    """The default site's root page, in the base language."""
    return Site.objects.get(is_default_site=True).root_page.specific


@pytest.fixture
def english_locale(db):
    """An added, not yet public, English locale."""
    return Locale.objects.create(language_code="en")


@pytest.fixture
def make_language_public(db):
    """Mark locales as public in the site's language settings."""

    def _make_public(*locales):
        language_settings = LanguageSettings.load()
        language_settings.public_locales.add(*locales)

    return _make_public


@pytest.fixture
def translate_page(db):
    """Create and publish a translation of a page, optionally with a new slug."""

    def _translate(page, locale, slug=None, publish=True):
        translated_page = page.copy_for_translation(locale)
        if slug is not None:
            translated_page.slug = slug
            translated_page.save()
        if publish:
            translated_page.save_revision().publish()
        return Page.objects.get(pk=translated_page.pk).specific

    return _translate


@pytest.fixture
def services_page(home_page):
    """A published child page of the home page, in the base language."""
    page = home_page.add_child(instance=Page(title="Servicios", slug="servicios"))
    page.save_revision().publish()
    return page


@pytest.fixture(autouse=True)
def _without_second_factor(settings, request):
    """Most tests use the admin without the second factor; tests/test_two_factor.py
    turns it on."""
    if request.node.get_closest_marker("two_factor") is None:
        settings.ORION_2FA_REQUIRED = False


@pytest.fixture(autouse=True)
def _renditions_in_the_same_thread(settings):
    """Generate image renditions synchronously, inside each test's transaction."""
    settings.ORION_IMAGE_RENDITIONS_IN_BACKGROUND = False


@pytest.fixture(autouse=True)
def _page_cache_off(settings, request, tmp_path):
    """An empty in-memory cache for each test; the page cache only where a test is
    marked page_cache."""
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    settings.ORION_PAGE_CACHE = (
        request.node.get_closest_marker("page_cache") is not None
    )
    # In-memory caches outlive a settings change: start each test empty.
    cache.clear()
    # WhiteNoise warns when STATIC_ROOT does not exist; tests never run collectstatic.
    static_root = tmp_path / "static"
    static_root.mkdir()
    settings.STATIC_ROOT = static_root
