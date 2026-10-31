import importlib
import re

import pytest
from django.apps import apps
from django.urls import reverse
from wagtail.models import Page, Site

from orion.core.blocks import ContentStreamBlock
from orion.pages.models import (
    ArticleIndexPage,
    ArticlePage,
    ContactPage,
    ContentPage,
    HomePage,
)
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db

welcome_migration = importlib.import_module(
    "orion.pages.migrations.0002_replace_welcome_page"
)


def _body(*blocks):
    stream_block = ContentStreamBlock()
    raw = [{"type": block_type, "value": value} for block_type, value in blocks]
    return stream_block.clean(stream_block.to_python(raw))


def _publish(parent, page):
    parent.add_child(instance=page)
    page.save_revision().publish()
    return page


def _main(client, page):
    html = client.get(page.url).content.decode()
    return html.split("<main", 1)[1].split("</main>", 1)[0]


class TestPlacement:
    def test_home_page_offers_the_orion_page_types(self, home_page):
        allowed = HomePage.allowed_subpage_models()

        for page_type in (ContentPage, ContactPage, ArticleIndexPage):
            assert page_type in allowed
        assert ArticlePage not in allowed

    def test_articles_only_go_in_listings(self, home_page):
        content_page = _publish(home_page, ContentPage(title="Nosotros"))
        index = _publish(home_page, ArticleIndexPage(title="Novedades"))

        assert not ArticlePage.can_create_at(content_page)
        assert ArticlePage.can_create_at(index)
        assert index.specific.allowed_subpage_models() == [ArticlePage]

    def test_contact_page_has_no_children(self, home_page):
        assert ContactPage.allowed_subpage_models() == []

    def test_second_home_page_cannot_be_created(self, home_page):
        assert not HomePage.can_create_at(Page.get_first_root_node())

    @pytest.mark.parametrize(
        ("model_name", "parent_name"),
        [
            ("contentpage", "home"),
            ("contactpage", "home"),
            ("articleindexpage", "home"),
            ("articlepage", "index"),
        ],
    )
    def test_admin_add_forms_open(
        self, admin_client, home_page, model_name, parent_name
    ):
        parents = {
            "home": home_page,
            "index": _publish(home_page, ArticleIndexPage(title="Novedades")),
        }

        response = admin_client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=["orion_pages", model_name, parents[parent_name].pk],
            )
        )

        assert response.status_code == 200


class TestSlugs:
    def test_page_slug_has_no_accents(self, home_page):
        page = ContentPage(title="Artículo de prueba")

        home_page.add_child(instance=page)

        assert page.slug == "articulo-de-prueba"


class TestMainHeading:
    def test_page_without_hero_shows_its_title(self, client, home_page):
        page = _publish(
            home_page,
            ContentPage(title="Nosotros", body=_body(("text", {"body": "<p>x</p>"}))),
        )

        headings = re.findall(r"<h1\b[^>]*>(.*?)</h1>", _main(client, page))

        assert headings == ["Nosotros"]

    def test_hero_holds_the_only_h1(self, client, home_page):
        page = _publish(
            home_page,
            ContentPage(
                title="Nosotros", body=_body(("hero", {"title": "<p>Bienvenidos</p>"}))
            ),
        )

        headings = re.findall(r"<h1\b[^>]*>(.*?)</h1>", _main(client, page))

        assert headings == ["Bienvenidos"]

    def test_hidden_hero_does_not_hold_the_h1(self, client, home_page):
        page = _publish(
            home_page,
            ContentPage(
                title="Nosotros",
                body=_body(("hero", {"title": "<p>Oculto</p>", "is_visible": False})),
            ),
        )

        headings = re.findall(r"<h1\b[^>]*>(.*?)</h1>", _main(client, page))

        assert headings == ["Nosotros"]


class TestContactPage:
    def test_shows_site_contact_data_and_follows_changes(self, client, home_page):
        site_settings = SiteSettings.load()
        site_settings.phone = "+595 21 729 1444"
        site_settings.save()
        page = _publish(
            home_page,
            ContactPage(
                title="Contacto", body=_body(("text", {"body": "<p>Hola</p>"}))
            ),
        )
        assert 'href="tel:+595217291444"' in _main(client, page)

        site_settings.phone = "+595 21 000 000"
        site_settings.save()

        html = _main(client, page)
        assert "+595 21 000 000" in html
        assert "<p>Hola</p>" in html


class TestInitialHomePage:
    @pytest.fixture
    def welcome_page(self, home_page):
        """A root page like the one Wagtail creates, set as the site's root."""
        page = Page(title=welcome_migration.WELCOME_TITLE, slug="bienvenida")
        Page.get_first_root_node().add_child(instance=page)
        site = Site.objects.get(is_default_site=True)
        site.root_page = page
        site.save()
        # Like a fresh install: no home page yet.
        home_page.delete()
        return page

    @staticmethod
    def _run_migration():
        welcome_migration.replace_welcome_page(apps, None)

    @staticmethod
    def _site_root():
        return Site.objects.get(is_default_site=True).root_page

    def test_fresh_install_has_a_home_page(self, home_page):
        assert isinstance(home_page, HomePage)
        assert not Page.objects.filter(title=welcome_migration.WELCOME_TITLE).exists()

    def test_untouched_welcome_page_is_replaced(self, welcome_page):
        site_id = Site.objects.get(is_default_site=True).pk

        self._run_migration()

        root = self._site_root()
        assert isinstance(root.specific, HomePage)
        assert root.path == welcome_page.path
        assert not Page.objects.filter(pk=welcome_page.pk).exists()
        assert Site.objects.get(is_default_site=True).pk == site_id

    def test_welcome_page_with_children_is_kept(self, welcome_page):
        welcome_page.add_child(instance=Page(title="Servicios", slug="servicios"))

        self._run_migration()

        assert self._site_root().pk == welcome_page.pk

    def test_translated_welcome_page_is_kept(self, welcome_page, english_locale):
        welcome_page.copy_for_translation(english_locale)

        self._run_migration()

        assert self._site_root().pk == welcome_page.pk

    def test_renamed_welcome_page_is_kept(self, welcome_page):
        welcome_page.title = "Mi sitio"
        welcome_page.save()

        self._run_migration()

        assert self._site_root().pk == welcome_page.pk
