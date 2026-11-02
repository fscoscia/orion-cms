import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from orion.editor.roles import ADMINISTRATORS_GROUP
from orion.pages.models import ArticleIndexPage, ArticlePage, ContentPage
from orion.snippets.models import CodeSnippet, CodeSnippetPage

pytestmark = pytest.mark.django_db

ADMIN_INDEX = "wagtailsnippets_orion_snippets_codesnippet:list"


def _page(parent, title, slug, page_class=ContentPage, **fields):
    page = page_class(title=title, slug=slug, **fields)
    parent.add_child(instance=page)
    page.save_revision().publish()
    return page


def _snippet(code="<script>analytics()</script>", **fields):
    pages = fields.pop("pages", [])
    page_types = fields.pop("page_types", [])
    locales = fields.pop("locales", [])
    snippet = CodeSnippet.objects.create(name="Analytics", code=code, **fields)
    for page in pages:
        CodeSnippetPage.objects.create(snippet=snippet, page=page)
    snippet.page_types.set(page_types)
    snippet.locales.set(locales)
    # ParentalManyToManyField values are written on save.
    snippet.save()
    return snippet


@pytest.fixture
def services(home_page):
    return _page(home_page, "Servicios", "servicios")


def _html(client, url):
    return client.get(url).content.decode()


class TestInsertion:
    @pytest.mark.parametrize(
        ("location", "before"),
        [
            ("head", "</head>"),
            ("body_start", "Skip to content"),
            ("body_end", "</body>"),
        ],
    )
    def test_locations(self, client, services, location, before):
        _snippet(code=f"<!-- {location} -->", location=location)

        html = _html(client, services.url)

        assert f"<!-- {location} -->" in html
        position = html.index(f"<!-- {location} -->")
        if location == "head":
            assert position < html.index("</head>")
        elif location == "body_start":
            assert html.index("<body") < position < html.index('id="main-content"')
        else:
            assert html.index("</footer>") < position < html.index("</body>")

    def test_inactive_is_not_loaded(self, client, services):
        _snippet(is_active=False)

        assert "analytics()" not in _html(client, services.url)

    def test_section_with_and_without_subpages(self, client, home_page, services):
        news = _page(home_page, "Novedades", "novedades", ArticleIndexPage)
        article = _page(news, "Nota", "nota", ArticlePage, summary="x")
        _snippet(code="<!-- con -->", scope="pages", pages=[news])
        _snippet(
            code="<!-- sin -->", scope="pages", pages=[news], include_subpages=False
        )

        assert "<!-- con -->" in _html(client, article.url)
        assert "<!-- sin -->" not in _html(client, article.url)
        assert "<!-- sin -->" in _html(client, news.url)
        assert "<!-- con -->" not in _html(client, services.url)

    def test_page_type(self, client, home_page, services):
        news = _page(home_page, "Novedades", "novedades", ArticleIndexPage)
        article = _page(news, "Nota", "nota", ArticlePage, summary="x")
        _snippet(
            scope="page_types",
            page_types=[ContentType.objects.get_for_model(ArticlePage)],
        )

        assert "analytics()" in _html(client, article.url)
        assert "analytics()" not in _html(client, services.url)

    def test_language(
        self, client, services, english_locale, make_language_public, translate_page
    ):
        make_language_public(english_locale)
        translate_page(services.get_parent(), english_locale)
        english = translate_page(services, english_locale, slug="services")
        _snippet(locales=[english_locale])

        assert "analytics()" in _html(client, english.url)
        assert "analytics()" not in _html(client, services.url)

    def test_view_without_a_page_gets_site_wide_only(self, client, services):
        _snippet(code="<!-- sitio -->")
        _snippet(code="<!-- seccion -->", scope="pages", pages=[services])

        html = _html(client, "/buscar/")

        assert "<!-- sitio -->" in html
        assert "<!-- seccion -->" not in html

    def test_emergency_switch(self, client, settings, services):
        settings.ORION_SCRIPTS_DISABLED = True
        _snippet()

        assert "analytics()" not in _html(client, services.url)

    def test_not_in_the_editor_preview(self, services):
        _snippet()

        response = services.make_preview_request()

        assert "analytics()" not in response.content.decode()

    def test_not_in_the_shared_preview(self, client, services):
        from django.utils import timezone

        from orion.editor.models import PreviewLink

        _snippet()
        link = PreviewLink.objects.create(
            page=services, expires_at=timezone.now() + timezone.timedelta(days=1)
        )

        html = _html(client, reverse("orion_shared_preview", args=[link.token]))

        assert "Servicios" in html
        assert "analytics()" not in html

    def test_not_in_the_admin(self, admin_client, services):
        _snippet()

        assert "analytics()" not in _html(admin_client, reverse("wagtailadmin_home"))

    @pytest.mark.page_cache
    def test_saving_refreshes_cached_pages(
        self, client, services, django_capture_on_commit_callbacks
    ):
        client.get(services.url)

        with django_capture_on_commit_callbacks(execute=True):
            _snippet()

        assert "analytics()" in _html(client, services.url)


class TestAdmin:
    def _form_data(self, **fields):
        data = {
            "name": "Chat",
            "code": "<script>chat()</script>",
            "location": "body_end",
            "is_active": "on",
            "scope": "site",
            "include_subpages": "on",
            "snippet_pages-TOTAL_FORMS": "0",
            "snippet_pages-INITIAL_FORMS": "0",
            "snippet_pages-MIN_NUM_FORMS": "0",
            "snippet_pages-MAX_NUM_FORMS": "1000",
        }
        data.update(fields)
        return data

    def test_superuser_creates_a_snippet(self, admin_client, services):
        response = admin_client.post(
            reverse("wagtailsnippets_orion_snippets_codesnippet:add"), self._form_data()
        )

        snippet = CodeSnippet.objects.get()
        assert response.status_code == 302
        assert snippet.revisions.count() == 1
        assert "chat()" in _html(admin_client, services.url)

    def test_pages_scope_needs_pages(self, admin_client):
        response = admin_client.post(
            reverse("wagtailsnippets_orion_snippets_codesnippet:add"),
            self._form_data(scope="pages"),
        )

        assert response.status_code == 200
        assert not CodeSnippet.objects.exists()

    def test_administrators_have_no_access(self, client, django_user_model, home_page):
        administrator = django_user_model.objects.create_user("jefa", password="x")
        administrator.groups.add(Group.objects.get(name=ADMINISTRATORS_GROUP))
        client.force_login(administrator)

        listing = client.get(reverse(ADMIN_INDEX))
        home = _html(client, reverse("wagtailadmin_home"))

        assert listing.status_code != 200
        assert '"orion_code_snippets"' not in home

    def test_group_with_the_permission(self, client, django_user_model, home_page):
        marketing = Group.objects.create(name="Marketing")
        marketing.permissions.add(
            Permission.objects.get(codename="access_admin"),
            *Permission.objects.filter(
                content_type__app_label="orion_snippets",
                content_type__model="codesnippet",
            ),
        )
        user = django_user_model.objects.create_user("marta", password="x")
        user.groups.add(marketing)
        client.force_login(user)

        assert client.get(reverse(ADMIN_INDEX)).status_code == 200

    def test_no_group_has_the_permission(self):
        assert not Group.objects.filter(
            permissions__content_type__app_label="orion_snippets"
        ).exists()

    def test_history_and_restore(self, admin_client, admin_user):
        snippet = _snippet(code="<!-- v1 -->")
        first = snippet.save_revision(user=admin_user)
        snippet.code = "<!-- v2 -->"
        snippet.save()
        snippet.save_revision(user=admin_user)

        history = _html(
            admin_client,
            reverse(
                "wagtailsnippets_orion_snippets_codesnippet:history", args=[snippet.pk]
            ),
        )
        restore = admin_client.get(
            reverse(
                "wagtailsnippets_orion_snippets_codesnippet:revisions_revert",
                args=[snippet.pk, first.pk],
            )
        )

        assert admin_user.get_username() in history
        assert restore.status_code == 200
        assert "&lt;!-- v1 --&gt;" in restore.content.decode()

    def test_emergency_switch_warning(self, admin_client, settings):
        settings.ORION_SCRIPTS_DISABLED = True

        html = _html(admin_client, reverse(ADMIN_INDEX))

        assert "ORION_SCRIPTS_DISABLED" in html


class TestContentSecurityPolicy:
    def test_snippets_carry_the_nonce(self, client, services):
        _snippet(
            code='<script async src="https://x.test/gtag.js"></script><style>p{}</style>'
        )

        response = client.get(services.url)

        nonce = response["Content-Security-Policy"].split("'nonce-")[1].split("'")[0]
        html = response.content.decode()
        assert f'<script nonce="{nonce}" async src="https://x.test/gtag.js">' in html
        assert f'<style nonce="{nonce}">p{{}}</style>' in html
