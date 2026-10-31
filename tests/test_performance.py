import re
from pathlib import Path

import pytest
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db import connection
from django.http import HttpResponse
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.utils.http import http_date
from wagtail.models import Page

import orion
from orion.core.cache import clear_page_cache, signals
from orion.core.cache.middleware import PageCacheMiddleware
from orion.navigation.models import Menu
from orion.pages.models import ContentPage
from orion.seo.models import NotFoundPath
from orion.settings.cache import parse_cache_url
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db

CACHE_HEADER = "X-Orion-Cache"


class TestCacheUrl:
    @pytest.mark.parametrize(
        ("url", "backend", "location"),
        [
            ("", "filebased.FileBasedCache", "orion-cache"),
            (
                "file:///var/cache/clinica",
                "filebased.FileBasedCache",
                "/var/cache/clinica",
            ),
            (
                "redis://127.0.0.1:6379/1",
                "redis.RedisCache",
                "redis://127.0.0.1:6379/1",
            ),
            ("rediss://cache.example:6380/0", "redis.RedisCache", "rediss://"),
            ("locmem://", "locmem.LocMemCache", None),
            ("dummy://", "dummy.DummyCache", None),
        ],
    )
    def test_schemes(self, url, backend, location):
        config = parse_cache_url(url, "secreto")

        assert config["BACKEND"].endswith(backend)
        if location:
            assert location in config["LOCATION"]

    def test_each_project_has_its_own_prefix(self):
        first = parse_cache_url("", "secreto-uno")["KEY_PREFIX"]
        second = parse_cache_url("", "secreto-dos")["KEY_PREFIX"]

        assert first != second
        assert "secreto" not in first

    def test_unknown_scheme(self):
        with pytest.raises(ImproperlyConfigured, match="redis://"):
            parse_cache_url("memcached://x", "secreto")


@pytest.fixture
def services(home_page):
    page = ContentPage(title="Servicios", slug="servicios")
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


def _publish(page, title, capture):
    page.title = title
    with capture(execute=True):
        page.save_revision().publish()


@pytest.mark.page_cache
class TestPageCache:
    def test_second_visit_is_served_from_the_cache(self, client, services):
        first = client.get(services.url)
        second = client.get(services.url)

        assert first[CACHE_HEADER] == "miss"
        assert second[CACHE_HEADER] == "hit"
        assert second.content == first.content
        assert second["Content-Type"] == first["Content-Type"]

    def test_query_string_is_part_of_the_key(self, client, services):
        client.get(services.url)

        assert client.get(f"{services.url}?page=2")[CACHE_HEADER] == "miss"

    def test_head_uses_the_cached_page(self, client, services):
        client.get(services.url)

        assert client.head(services.url)[CACHE_HEADER] == "hit"

    def test_signed_in_users_skip_the_cache(self, admin_client, client, services):
        response = admin_client.get(services.url)

        assert CACHE_HEADER not in response
        assert client.get(services.url)[CACHE_HEADER] == "miss"

    def test_not_found_is_not_cached(self, client, home_page):
        client.get("/no-existe/")

        assert CACHE_HEADER not in client.get("/no-existe/")

    def test_turned_off(self, client, settings, services):
        settings.ORION_PAGE_CACHE = False
        client.get(services.url)

        assert CACHE_HEADER not in client.get(services.url)

    def test_editor_preview_is_not_cached(self, client, services):
        services.make_preview_request()

        assert client.get(services.url)[CACHE_HEADER] == "miss"


@pytest.mark.page_cache
class TestUncacheableResponses:
    def _visit(self, path="/servicios/", response=None, **request_fields):
        request = RequestFactory().get(path)
        for name, value in request_fields.items():
            setattr(request, name, value)
        calls = []

        def view(_request):
            calls.append(1)
            return response() if response else HttpResponse("hola")

        middleware = PageCacheMiddleware(view)
        middleware(request)
        middleware(request)
        return len(calls)

    def _response_with(self, **headers):
        def build():
            response = HttpResponse("hola")
            for name, value in headers.items():
                response[name.replace("_", "-")] = value
            return response

        return build

    def test_cacheable(self):
        assert self._visit() == 1

    def test_cookies(self):
        def build():
            response = HttpResponse("hola")
            response.set_cookie("csrftoken", "x")
            return response

        assert self._visit(response=build) == 2

    def test_csrf_token(self):
        request = RequestFactory().get("/servicios/")
        calls = []

        def view(view_request):
            calls.append(1)
            view_request.META["CSRF_COOKIE_NEEDS_UPDATE"] = True
            return HttpResponse("form")

        middleware = PageCacheMiddleware(view)
        middleware(request)
        middleware(RequestFactory().get("/servicios/"))

        assert len(calls) == 2

    @pytest.mark.parametrize("directive", ["private", "no-store", "no-cache"])
    def test_cache_control(self, directive):
        response = self._response_with(Cache_Control=directive)

        assert self._visit(response=response) == 2

    def test_dummy_request_of_a_preview(self):
        assert self._visit(is_dummy=True) == 2

    @pytest.mark.parametrize(
        "path", ["/admin/pages/", "/_preview/abc/", "/static/x.css", "/media/x.jpg"]
    )
    def test_excluded_paths(self, path):
        assert self._visit(path=path) == 2

    def test_session_cookie(self, settings):
        request = RequestFactory().get("/servicios/")
        request.COOKIES[settings.SESSION_COOKIE_NAME] = "abc"
        calls = []
        middleware = PageCacheMiddleware(
            lambda _request: calls.append(1) or HttpResponse("hola")
        )

        middleware(request)
        middleware(request)

        assert len(calls) == 2


@pytest.mark.page_cache
class TestConditionalRequests:
    def test_etag_revalidation(self, client, services):
        etag = client.get(services.url)["ETag"]

        cached = client.get(services.url, headers={"if-none-match": etag})

        assert cached.status_code == 304

    def test_last_modified_revalidation(self, client, services):
        last_modified = client.get(services.url)["Last-Modified"]

        cached = client.get(services.url, headers={"if-modified-since": last_modified})

        assert cached.status_code == 304

    def test_etag_without_the_page_cache(self, client, settings, services):
        settings.ORION_PAGE_CACHE = False
        etag = client.get(services.url)["ETag"]

        assert (
            client.get(services.url, headers={"if-none-match": etag}).status_code == 304
        )

    def test_old_date_downloads_again(self, client, services):
        client.get(services.url)

        response = client.get(services.url, headers={"if-modified-since": http_date(0)})

        assert response.status_code == 200


@pytest.mark.page_cache
class TestInvalidation:
    def test_publishing_empties_the_cache(
        self, client, services, home_page, django_capture_on_commit_callbacks
    ):
        client.get(services.url)
        client.get(home_page.url)

        _publish(services, "Servicios nuevos", django_capture_on_commit_callbacks)

        response = client.get(services.url)
        assert response[CACHE_HEADER] == "miss"
        assert "Servicios nuevos" in response.content.decode()
        assert client.get(home_page.url)[CACHE_HEADER] == "miss"

    def test_unpublishing(self, client, services, django_capture_on_commit_callbacks):
        client.get(services.url)

        with django_capture_on_commit_callbacks(execute=True):
            services.unpublish()

        assert client.get(services.url).status_code == 404

    def test_deleting(self, client, services, django_capture_on_commit_callbacks):
        url = services.url
        client.get(url)

        with django_capture_on_commit_callbacks(execute=True):
            services.delete()

        assert client.get(url).status_code == 404

    def test_scheduled_publishing(
        self, client, services, django_capture_on_commit_callbacks
    ):
        client.get(services.url)
        services.title = "Servicios programados"
        revision = services.save_revision()
        type(revision).objects.filter(pk=revision.pk).update(
            approved_go_live_at=revision.created_at
        )

        with django_capture_on_commit_callbacks(execute=True):
            call_command("publish_scheduled")

        assert "Servicios programados" in client.get(services.url).content.decode()

    @pytest.mark.parametrize("model", [Menu, SiteSettings])
    def test_site_data_and_menus(
        self, client, services, model, django_capture_on_commit_callbacks
    ):
        client.get(services.url)

        with django_capture_on_commit_callbacks(execute=True):
            if model is Menu:
                Menu.objects.create(location="header")
            else:
                SiteSettings.load().save()

        assert client.get(services.url)[CACHE_HEADER] == "miss"

    def test_project_models(
        self, settings, client, services, django_capture_on_commit_callbacks
    ):
        settings.ORION_PAGE_CACHE_MODELS = ["orion_seo.NotFoundPath"]
        signals.connect()
        client.get(services.url)

        with django_capture_on_commit_callbacks(execute=True):
            NotFoundPath.objects.create(site=services.get_site(), path="/x/")

        assert client.get(services.url)[CACHE_HEADER] == "miss"

    def test_command(self, client, services, django_capture_on_commit_callbacks):
        client.get(services.url)

        with django_capture_on_commit_callbacks(execute=True):
            call_command("orion_clear_page_cache")

        assert client.get(services.url)[CACHE_HEADER] == "miss"

    def test_other_cache_entries_are_kept(self, django_capture_on_commit_callbacks):
        cache.set("otra-cosa", 42)

        with django_capture_on_commit_callbacks(execute=True):
            clear_page_cache()

        assert cache.get("otra-cosa") == 42

    def test_drafts_do_not_empty_it(self, client, services):
        client.get(services.url)
        services.title = "Borrador"
        services.save_revision()

        assert client.get(services.url)[CACHE_HEADER] == "hit"
        assert Page.objects.get(pk=services.pk).title == "Servicios"


class TestMenuCache:
    @pytest.fixture
    def menu(self, services):
        return Menu.objects.create(
            location="header",
            items=[
                {
                    "type": "item",
                    "value": {"link": {"page": services.pk}, "subitems": []},
                }
            ],
        )

    def test_second_page_does_not_query_the_menu(
        self, client, home_page, services, menu
    ):
        client.get(home_page.url)
        with CaptureQueriesContext(connection) as queries:
            html = client.get(services.url).content.decode()

        menu_table = Menu._meta.db_table
        assert not [q for q in queries if menu_table in q["sql"]]
        assert re.search(r'<a href="/servicios/"[^>]*aria-current="page"', html)

    def test_current_item_changes_with_the_page(
        self, client, home_page, services, menu
    ):
        client.get(services.url)

        html = client.get(home_page.url).content.decode()

        assert 'href="/servicios/"' in html
        assert not re.search(r'<a href="/servicios/"[^>]*aria-current="page"', html)

    def test_menu_change_is_visible(
        self, client, home_page, services, menu, django_capture_on_commit_callbacks
    ):
        client.get(home_page.url)
        menu.items = []

        with django_capture_on_commit_callbacks(execute=True):
            menu.save()

        assert 'href="/servicios/"' not in client.get(home_page.url).content.decode()


class TestFontPreload:
    def test_listed_fonts_are_preloaded(self, client, settings, home_page):
        settings.ORION_FONT_PRELOAD = ["mi_sitio/fonts/marca.woff2"]

        head = client.get(home_page.url).content.decode().split("</head>", 1)[0]

        assert (
            '<link rel="preload" href="/static/mi_sitio/fonts/marca.woff2" as="font" '
            'type="font/woff2" crossorigin>'
        ) in head

    def test_nothing_without_the_setting(self, client, home_page):
        head = client.get(home_page.url).content.decode().split("</head>", 1)[0]

        assert 'as="font"' not in head


def test_static_files_do_not_reference_missing_source_maps():
    """collectstatic with hashed names fails on a reference to a missing file."""
    static_dir = Path(orion.__file__).parent
    for path in static_dir.glob("*/static/**/*"):
        if path.suffix not in (".js", ".css"):
            continue
        for reference in re.findall(r"sourceMappingURL=(\S+)", path.read_text()):
            assert (path.parent / reference).exists(), f"{path}: {reference}"
