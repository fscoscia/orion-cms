import re

import pytest
from django.core.exceptions import ValidationError
from wagtail.models import Locale, Page

from orion.navigation.models import Menu, MenuLocation

pytestmark = pytest.mark.django_db


def _menu(location=MenuLocation.HEADER, locale=None, items=()):
    menu = Menu(location=location, items=list(items))
    if locale is not None:
        menu.locale = locale
    menu.save()
    return menu


def _item(link, subitems=()):
    # Raw StreamField data, which accepts page ids like the admin form does.
    return {"type": "item", "value": {"link": link, "subitems": list(subitems)}}


@pytest.fixture
def clinic_page(services_page):
    page = services_page.add_child(
        instance=Page(title="Consultorios", slug="consultorios")
    )
    page.save_revision().publish()
    return page


class TestStructure:
    def test_one_menu_per_location_and_language(self):
        _menu()
        # The admin sets the locale before validating; Wagtail only defaults it on save.
        duplicate = Menu(location=MenuLocation.HEADER, locale=Locale.get_default())

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_header_and_footer_coexist(self):
        _menu(MenuLocation.HEADER)
        footer = Menu(location=MenuLocation.FOOTER)

        footer.full_clean()

    def test_item_with_submenu_is_rendered(self, client, services_page, clinic_page):
        _menu(
            items=[
                _item(
                    {"page": services_page.pk},
                    subitems=[{"page": clinic_page.pk}],
                )
            ]
        )

        html = client.get("/").content.decode()

        assert 'href="/servicios/"' in html
        assert 'href="/servicios/consultorios/"' in html


class TestVisibility:
    def test_unpublished_page_item_is_hidden(self, client, services_page):
        _menu(items=[_item({"page": services_page.pk})])
        services_page.unpublish()

        assert 'href="/servicios/"' not in client.get("/").content.decode()

    def test_group_label_shows_with_visible_subitems(self, client, services_page):
        _menu(
            items=[
                _item({"label": "Institucional"}, subitems=[{"page": services_page.pk}])
            ]
        )

        html = client.get("/").content.decode()

        assert "Institucional" in html
        assert 'href="/servicios/"' in html

    def test_group_label_without_visible_subitems_is_hidden(
        self, client, services_page
    ):
        _menu(
            items=[
                _item({"label": "Institucional"}, subitems=[{"page": services_page.pk}])
            ]
        )
        services_page.unpublish()

        assert "Institucional" not in client.get("/").content.decode()


class TestCurrentPage:
    def test_ancestor_item_is_marked_current(self, client, services_page, clinic_page):
        _menu(items=[_item({"page": services_page.pk})])

        html = client.get("/servicios/consultorios/").content.decode()

        link_tag = re.search(r'<a href="/servicios/"[^>]*>', html).group()
        assert 'aria-current="page"' in link_tag

    def test_item_with_an_anchor_is_not_marked(self, client, services_page):
        _menu(items=[_item({"page": services_page.pk, "anchor": "precios"})])

        html = client.get("/servicios/").content.decode()

        link_tag = re.search(r'<a href="/servicios/#precios"[^>]*>', html).group()
        assert "aria-current" not in link_tag

    def test_subitem_with_an_anchor_does_not_mark_its_parent(
        self, client, home_page, services_page
    ):
        _menu(
            items=[
                _item(
                    {"label": "Grupo", "url": "https://example.org/"},
                    [
                        {
                            "page": services_page.pk,
                            "anchor": "precios",
                            "label": "Precios",
                        }
                    ],
                )
            ]
        )

        html = client.get("/servicios/").content.decode()

        assert (
            "aria-current" not in re.search(r"<nav[^>]*>.*?</nav>", html, re.S).group()
        )


class TestTranslation:
    @pytest.fixture
    def english_site(
        self,
        home_page,
        services_page,
        english_locale,
        make_language_public,
        translate_page,
    ):
        make_language_public(english_locale)
        translate_page(home_page, english_locale)
        translate_page(services_page, english_locale, slug="services")
        return english_locale

    def test_translated_menu_shows_translated_labels(
        self, client, services_page, english_site
    ):
        base_menu = _menu(
            items=[_item({"label": "Servicios", "page": services_page.pk})]
        )
        english_menu = base_menu.copy_for_translation(english_site)
        english_menu.items = [_item({"label": "Services", "page": services_page.pk})]
        english_menu.save()

        html = client.get("/en/").content.decode()

        assert ">Services<" in html

    def test_untranslated_menu_falls_back_with_translated_pages(
        self, client, services_page, english_site
    ):
        _menu(items=[_item({"page": services_page.pk})])

        html = client.get("/en/").content.decode()

        assert 'href="/en/services/"' in html
