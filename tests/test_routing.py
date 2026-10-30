import importlib
from contextlib import ExitStack

import pytest
from django.test import override_settings
from django.urls import clear_url_caches
from wagtail.models import Page, Site

import example.urls
import orion.urls

pytestmark = pytest.mark.django_db


def _reload_urls():
    importlib.reload(orion.urls)
    importlib.reload(example.urls)
    clear_url_caches()


@pytest.fixture
def serve_admin_at():
    """Serve the admin at a given path for the rest of the test.

    The URL configuration reads the setting at import, so it is rebuilt after the
    override and again only once the original value is restored; relying on the
    teardown order of separate fixtures left the custom path behind for later tests.
    """
    overrides = ExitStack()

    def _serve(admin_path):
        overrides.enter_context(override_settings(ORION_ADMIN_PATH=admin_path))
        _reload_urls()

    yield _serve
    overrides.close()
    _reload_urls()


class TestAdminPath:
    def test_admin_login_uses_default_path(self, client, serve_admin_at):
        # The suite's settings come from the environment, so the default is set
        # explicitly here; test_settings_base checks the value without the variable.
        serve_admin_at("admin/")

        response = client.get("/admin/login/")

        assert response.status_code == 200

    def test_admin_moves_to_custom_path(self, client, serve_admin_at):
        serve_admin_at("panel/")

        assert client.get("/panel/login/").status_code == 200
        assert client.get("/admin/login/").status_code == 404


class TestPageServing:
    def test_site_root_serves_the_root_page(self, client):
        root_page = Site.objects.get(is_default_site=True).root_page

        response = client.get("/")

        assert response.status_code == 200
        assert root_page.title in response.content.decode()

    def test_generic_page_uses_orion_base_template(self, client, settings):
        settings.LANGUAGE_CODE = "es"
        root_page = Site.objects.get(is_default_site=True).root_page
        child_page = root_page.add_child(
            instance=Page(title="Página de prueba", slug="pagina-de-prueba")
        )

        response = client.get(child_page.url)
        html = response.content.decode()

        assert response.status_code == 200
        assert '<html lang="es"' in html
        assert "<title>Página de prueba</title>" in html
        assert 'name="viewport"' in html
        assert 'id="main-content"' in html

    def test_page_language_ignores_the_browser(self, client, settings):
        settings.LANGUAGE_CODE = "es"

        response = client.get("/", HTTP_ACCEPT_LANGUAGE="fr")

        assert '<html lang="es"' in response.content.decode()
