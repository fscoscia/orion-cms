import re

import pytest
from django.contrib.auth.models import Group
from django.db import connection
from django.urls import reverse
from wagtail.contrib.search_promotions.models import Query, SearchPromotion

from orion.core.blocks import ContentStreamBlock
from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.pages.models import ArticleIndexPage, ArticlePage, ContentPage
from orion.search.backend import has_trigram
from orion.search.models import NoResultsQuery

# MySQL's FULLTEXT indexes only see committed rows, so these tests commit.
pytestmark = pytest.mark.django_db(transaction=True, serialized_rollback=True)

SEARCH = "/buscar/"


def _body(text):
    stream_block = ContentStreamBlock()
    return stream_block.clean(
        stream_block.to_python([{"type": "text", "value": {"body": f"<p>{text}</p>"}}])
    )


def _page(parent, title, slug, text="", page_class=ContentPage, **fields):
    if text and page_class is ContentPage:
        fields["body"] = _body(text)
    page = page_class(title=title, slug=slug, **fields)
    parent.add_child(instance=page)
    page.save_revision().publish()
    return page


def _titles(html):
    return re.findall(r'<h2 class="text-xl font-semibold"><a [^>]*>([^<]+)</a>', html)


def _search(client, query, **params):
    return client.get(SEARCH, {"q": query, **params}).content.decode()


@pytest.fixture
def services(home_page):
    return _page(home_page, "Servicios", "servicios", "Hacemos radiografías digitales.")


class TestIndex:
    def test_text_inside_a_block(self, client, services):
        assert _titles(_search(client, "radiografías")) == ["Servicios"]

    def test_article_summary(self, client, home_page):
        index = _page(home_page, "Novedades", "novedades", page_class=ArticleIndexPage)
        _page(
            index,
            "Nueva sede",
            "nueva-sede",
            page_class=ArticlePage,
            summary="Abrimos una sede en Luque.",
        )

        assert _titles(_search(client, "Luque")) == ["Nueva sede"]

    def test_draft_is_not_found(self, client, services):
        services.body = _body("Palabra secreta del borrador.")
        services.save_revision()

        assert _titles(_search(client, "secreta")) == []

    def test_not_indexed_pages_are_left_out(self, client, home_page):
        _page(home_page, "Gracias", "gracias", "Radiografías listas.", no_index=True)

        assert _titles(_search(client, "radiografías")) == []

    def test_other_language_is_left_out(
        self, client, services, english_locale, make_language_public, translate_page
    ):
        make_language_public(english_locale)
        translate_page(services.get_parent(), english_locale)
        translate_page(services, english_locale, slug="services")

        html = client.get("/en/search/", {"q": "radiografías"}).content.decode()

        # The translation copies the text: the result is the English page only.
        assert re.findall(
            r'<h2 class="text-xl font-semibold"><a [^>]*href="([^"]+)"', html
        ) == ["/en/services/"]

    def test_config_follows_the_base_language(self, settings):
        backend = settings.WAGTAILSEARCH_BACKENDS["default"]

        assert backend["SEARCH_CONFIG"] == settings.ORION_SEARCH_CONFIG == "spanish"

    @pytest.mark.skipif(
        connection.vendor != "postgresql", reason="Stemming needs PostgreSQL"
    )
    def test_plural_matches_in_postgresql(self, client, home_page):
        _page(
            home_page, "Equipo", "equipo", "Nuestro médico atiende de lunes a viernes."
        )

        assert _titles(_search(client, "médicos")) == ["Equipo"]

    def test_works_without_the_trigram_extension(self, client, services):
        assert isinstance(has_trigram(), bool)
        assert "No se encontró nada" in _search(client, "radiografias-inexistentes")


class TestResultsPage:
    def test_result_shows_title_summary_and_type(self, client, home_page):
        _page(
            home_page,
            "Turnos",
            "turnos",
            "Pedí tu turno online.",
            search_description="Cómo pedir un turno.",
        )

        html = _search(client, "turno")

        assert _titles(html) == ["Turnos"]
        assert "Cómo pedir un turno." in html
        assert "Página" in html
        assert 'value="turno"' in html
        assert '<meta name="robots" content="noindex">' in html

    def test_type_filter(self, client, home_page, services):
        index = _page(home_page, "Novedades", "novedades", page_class=ArticleIndexPage)
        _page(
            index,
            "Radiografías en casa",
            "radiografias-en-casa",
            page_class=ArticlePage,
            summary="Ahora hacemos radiografías a domicilio.",
        )

        articles = _titles(_search(client, "radiografías", type="article"))
        pages = _titles(_search(client, "radiografías", type="page"))

        assert articles == ["Radiografías en casa"]
        assert pages == ["Servicios"]

    def test_pagination(self, client, home_page):
        for number in range(12):
            _page(home_page, f"Sede {number}", f"sede-{number}", "Atención de guardia.")

        first = _search(client, "guardia")
        second = _search(client, "guardia", page=2)

        assert len(_titles(first)) == 10
        assert len(_titles(second)) == 2
        assert "Página 1 de 2" in first

    def test_without_a_query(self, client, services):
        html = client.get(SEARCH).content.decode()

        assert 'name="q"' in html
        assert _titles(html) == []

    def test_nothing_found(self, client, services):
        assert "No se encontró nada" in _search(client, "estacionamiento")

    def test_promoted_first(self, client, home_page, services):
        online = _page(home_page, "Turnos online", "turnos-online", "Sistema nuevo.")
        query = Query.get("radiografías")
        SearchPromotion.objects.create(
            query=query, page=online, description="Pedí tu turno."
        )

        html = _search(client, "Radiografías")

        assert _titles(html) == ["Turnos online", "Servicios"]
        assert "Destacado" in html

    def test_english_route(self, client, english_locale, make_language_public):
        make_language_public(english_locale)

        assert reverse("orion_search") == SEARCH
        assert client.get("/en/search/").status_code == 200


class TestHeader:
    def test_form_in_the_header(self, client, home_page):
        html = client.get(home_page.url).content.decode()
        header = html.split("</header>", 1)[0]

        assert f'action="{SEARCH}"' in header
        assert 'role="search"' in header

    def test_can_be_turned_off(self, client, settings, home_page):
        settings.ORION_SEARCH_IN_HEADER = False

        header = client.get(home_page.url).content.decode().split("</header>", 1)[0]

        assert 'role="search"' not in header


class TestPromotionsAndReport:
    def _user(self, django_user_model, name, group_name):
        user = django_user_model.objects.create_user(name, password="x")
        user.groups.add(Group.objects.get(name=group_name))
        return user

    def test_editors_manage_promotions(self, client, django_user_model):
        client.force_login(self._user(django_user_model, "ana", EDITORS_GROUP))

        response = client.get(reverse("wagtailsearchpromotions:add"))

        assert response.status_code == 200

    def test_searches_are_recorded(self, client, services):
        _search(client, "radiografías")
        _search(client, "radiografías")
        _search(client, "estacionamiento")

        assert Query.get("radiografías").hits == 2
        assert NoResultsQuery.objects.get(query_string="estacionamiento").hits == 1

    def test_no_results_limit(self, client, settings, services):
        settings.ORION_SEARCH_MAX_NO_RESULTS = 1

        _search(client, "uno")
        _search(client, "dos")

        assert list(NoResultsQuery.objects.values_list("query_string", flat=True)) == [
            "uno"
        ]

    def test_report_for_administrators(self, client, django_user_model, services):
        _search(client, "estacionamiento")
        client.force_login(self._user(django_user_model, "jefa", ADMINISTRATORS_GROUP))

        html = client.get(reverse("orion_search_report")).content.decode()
        home = client.get(reverse("wagtailadmin_home")).content.decode()

        assert "estacionamiento" in html
        assert '"orion_searches"' in home

    def test_editors_do_not_see_the_report(self, client, django_user_model, home_page):
        client.force_login(self._user(django_user_model, "ana", EDITORS_GROUP))

        assert client.get(reverse("orion_search_report")).status_code != 200
