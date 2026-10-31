import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from orion.navigation.models import Menu, MenuLocation
from orion.pages.models import ArticleIndexPage, ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture
def editor_client(client, django_user_model):
    editor = django_user_model.objects.create_user(
        "editora", password="x", first_name="Ana"
    )
    editor.groups.add(Group.objects.get(name="Editores"))
    client.force_login(editor)
    return client


@pytest.fixture
def add_listing(home_page):
    def _add(title, slug):
        listing = ArticleIndexPage(title=title, slug=slug)
        home_page.add_child(instance=listing)
        listing.save_revision().publish()
        return listing

    return _add


def _dashboard(client):
    return client.get(reverse("wagtailadmin_home")).content.decode()


def _action_titles(html):
    section = html.split('class="orion-welcome"', 1)[1].split("</section>", 1)[0]
    return [
        title.split("</strong>", 1)[0].strip()
        for title in section.split("<strong>")[1:]
    ]


class TestWelcomePanel:
    def test_superuser_sees_every_action(self, admin_client, add_listing):
        add_listing("Novedades", "novedades")

        assert len(_action_titles(_dashboard(admin_client))) == 6

    def test_editor_sees_actions_by_permission(self, editor_client, add_listing):
        add_listing("Novedades", "novedades")

        html = _dashboard(editor_client)

        assert "Ana" in html
        assert len(_action_titles(html)) == 5
        assert reverse("wagtailsnippets_orion_navigation_menu:list") in html
        assert "/admin/settings/orion_site_data/" not in html

    def test_without_listings_there_is_no_article_action(self, admin_client, home_page):
        html = _dashboard(admin_client)

        assert len(_action_titles(html)) == 5
        assert reverse("orion_editor_new_article") not in html

    def test_draft_changes_are_listed(self, admin_client, home_page):
        page = ContentPage(title="Nosotros", slug="nosotros")
        home_page.add_child(instance=page)
        page.save_revision().publish()
        page.title = "Nosotros (borrador)"
        page.save_revision()

        html = _dashboard(admin_client)

        assert reverse("wagtailadmin_pages:edit", args=[page.pk]) in html
        assert "Nosotros (borrador)" in html

    def test_counters_are_removed(self, admin_client, home_page):
        assert "w-summary__list" not in _dashboard(admin_client)


class TestNewArticle:
    def test_one_listing_opens_the_form(self, admin_client, add_listing):
        listing = add_listing("Novedades", "novedades")

        response = admin_client.get(reverse("orion_editor_new_article"))

        assert response.status_code == 302
        assert response["Location"] == reverse(
            "wagtailadmin_pages:add", args=["orion_pages", "articlepage", listing.pk]
        )

    def test_several_listings_ask_for_one(self, admin_client, add_listing):
        add_listing("Novedades", "novedades")
        add_listing("Blog", "blog")

        html = admin_client.get(reverse("orion_editor_new_article")).content.decode()

        assert "Novedades" in html
        assert "Blog" in html

    def test_without_listings_it_is_not_found(self, admin_client, home_page):
        response = admin_client.get(reverse("orion_editor_new_article"))

        assert response.status_code == 404


class TestMenu:
    def test_editor_menu_has_shortcuts_and_no_admin_items(
        self, editor_client, add_listing
    ):
        add_listing("Novedades", "novedades")

        html = _dashboard(editor_client)

        assert '"orion_new_article"' in html
        assert '"orion_view_site"' in html
        assert '"reports"' not in html
        assert '"help"' not in html

    def test_administrators_group_sees_reports_and_help(
        self, client, django_user_model, home_page
    ):
        administrator = django_user_model.objects.create_user("jefa", password="x")
        administrator.groups.add(Group.objects.get(name="Administradores"))
        client.force_login(administrator)

        html = _dashboard(client)

        assert '"reports"' in html
        assert '"help"' in html

    def test_superuser_keeps_reports_and_help(self, admin_client, home_page):
        html = _dashboard(admin_client)

        # Also guards the names this change hides, which Wagtail could rename.
        assert '"reports"' in html
        assert '"help"' in html
        assert '"orion_new_article"' not in html


class TestSiteBar:
    def test_links_to_the_menus_and_texts_of_the_visited_language(
        self,
        editor_client,
        home_page,
        english_locale,
        make_language_public,
        translate_page,
    ):
        make_language_public(english_locale)
        translate_page(home_page, english_locale)
        footer_en = Menu.objects.create(
            location=MenuLocation.FOOTER, locale=english_locale
        )

        html = editor_client.get("/en/").content.decode()

        footer_edit = reverse(
            "wagtailsnippets_orion_navigation_menu:edit", args=[footer_en.pk]
        )
        assert f'href="{footer_edit}"' in html
        assert (
            f'href="{reverse("wagtailsnippets_orion_navigation_menu:add")}'
            "?locale=en&amp;location=header" in html
        )
        assert reverse("wagtailsnippets_orion_site_data_sitetexts:add") in html

    def test_without_permission_there_are_no_links(
        self, client, django_user_model, home_page
    ):
        user = django_user_model.objects.create_user("lectora", password="x")
        user.user_permissions.add(Permission.objects.get(codename="access_admin"))
        client.force_login(user)

        html = client.get("/").content.decode()

        assert reverse("wagtailsnippets_orion_navigation_menu:add") not in html
