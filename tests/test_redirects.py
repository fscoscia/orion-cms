import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Site

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.pages.models import ContentPage
from orion.seo.models import NotFoundPath

pytestmark = pytest.mark.django_db


@pytest.fixture
def make_user(django_user_model):
    def _make(username, group_name):
        user = django_user_model.objects.create_user(username, password="x")
        user.groups.add(Group.objects.get(name=group_name))
        return user

    return _make


@pytest.fixture
def services(home_page):
    page = ContentPage(title="Servicios", slug="servicios")
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


@pytest.fixture
def site():
    return Site.objects.get(is_default_site=True)


class TestRedirects:
    def test_old_path_redirects_permanently(self, client, services):
        Redirect.objects.create(old_path="/viejo-servicio", redirect_page=services)

        response = client.get("/viejo-servicio/")

        assert response.status_code == 301
        assert response["Location"].endswith("/servicios/")

    def test_changing_the_slug_creates_a_redirect(
        self, client, services, django_capture_on_commit_callbacks
    ):
        services.slug = "nuestros-servicios"
        # Wagtail creates the redirect once the change is committed.
        with django_capture_on_commit_callbacks(execute=True):
            services.save_revision().publish()

        response = client.get("/servicios/")

        assert response.status_code == 301
        assert response["Location"].endswith("/nuestros-servicios/")

    def test_administrators_manage_and_import(self, client, make_user):
        client.force_login(make_user("jefa", ADMINISTRATORS_GROUP))

        assert client.get(reverse("wagtailredirects:index")).status_code == 200
        assert client.get(reverse("wagtailredirects:add")).status_code == 200
        assert client.get(reverse("wagtailredirects:start_import")).status_code == 200

    def test_editors_do_not(self, client, make_user, home_page):
        client.force_login(make_user("ana", EDITORS_GROUP))

        html = client.get(reverse("wagtailadmin_home")).content.decode()

        assert client.get(reverse("wagtailredirects:index")).status_code != 200
        assert reverse("wagtailredirects:index") not in html


class TestNotFoundRecording:
    def test_counts_visits(self, client, home_page):
        for _visit in range(3):
            client.get("/promo-2024/?utm_source=x")

        recorded = NotFoundPath.objects.get()
        assert recorded.path == "/promo-2024/"
        assert recorded.hits == 3

    @pytest.mark.parametrize(
        "path", ["/static/nada.css", "/media/nada.jpg", "/_preview/nada/"]
    )
    def test_ignored_paths(self, client, home_page, path):
        client.get(path)

        assert not NotFoundPath.objects.exists()

    def test_admin_paths_are_ignored(self, admin_client, settings, home_page):
        admin_client.get(f"/{settings.ORION_ADMIN_PATH}no-existe/")

        assert not NotFoundPath.objects.exists()

    def test_other_methods_are_ignored(self, client, home_page):
        client.post("/promo-2024/")

        assert not NotFoundPath.objects.exists()

    def test_redirected_paths_are_not_recorded(self, client, services):
        Redirect.objects.create(old_path="/viejo", redirect_page=services)

        client.get("/viejo/")

        assert not NotFoundPath.objects.exists()

    def test_limit_of_distinct_paths(self, client, settings, home_page):
        settings.ORION_404_MAX_PATHS = 2
        for path in ("/a/", "/b/", "/c/", "/a/"):
            client.get(path)

        hits = dict(NotFoundPath.objects.values_list("path", "hits"))
        assert hits == {"/a/": 2, "/b/": 1}


class TestMonitor:
    @pytest.fixture
    def not_found(self, site):
        return NotFoundPath.objects.create(site=site, path="/promo-2024/", hits=5)

    def test_listed_for_administrators(self, client, make_user, not_found):
        client.force_login(make_user("jefa", ADMINISTRATORS_GROUP))

        html = client.get(reverse("orion_not_found_index")).content.decode()
        home = client.get(reverse("wagtailadmin_home")).content.decode()

        assert "/promo-2024/" in html
        assert '"orion_not_found"' in home

    def test_redirect_from_the_monitor(
        self, client, make_user, not_found, home_page, site
    ):
        promotions = ContentPage(title="Promociones", slug="promociones")
        home_page.add_child(instance=promotions)
        promotions.save_revision().publish()
        client.force_login(make_user("jefa", ADMINISTRATORS_GROUP))
        url = reverse("orion_not_found_redirect", args=[not_found.pk])

        form = client.get(url).content.decode()
        response = client.post(
            url,
            {
                "old_path": "/promo-2024/",
                "site": site.pk,
                "is_permanent": "on",
                "redirect_page": promotions.pk,
            },
        )
        client.logout()

        assert 'value="/promo-2024/"' in form
        assert response.status_code == 302
        assert not NotFoundPath.objects.exists()
        visit = client.get("/promo-2024/")
        assert visit.status_code == 301
        assert visit["Location"].endswith("/promociones/")

    def test_discard(self, client, make_user, not_found):
        client.force_login(make_user("jefa", ADMINISTRATORS_GROUP))

        client.post(reverse("orion_not_found_discard", args=[not_found.pk]))

        assert not NotFoundPath.objects.exists()

    def test_editors_cannot(self, client, make_user, not_found):
        client.force_login(make_user("ana", EDITORS_GROUP))

        listing = client.get(reverse("orion_not_found_index"))
        client.post(reverse("orion_not_found_discard", args=[not_found.pk]))
        home = client.get(reverse("wagtailadmin_home")).content.decode()

        assert listing.status_code != 200
        assert NotFoundPath.objects.exists()
        assert '"orion_not_found"' not in home

    def test_redirect_created_elsewhere_clears_the_path(self, not_found, services):
        Redirect.objects.create(old_path="/promo-2024", redirect_page=services)

        assert not NotFoundPath.objects.exists()
