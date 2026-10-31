import re

import pytest
from django.urls import reverse
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from orion.editor.checks import check_admin_colors
from orion.editor.colors import contrast_with_white, hex_to_hsl
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db


@pytest.fixture
def site_name(home_page):
    site = Site.objects.get(is_default_site=True)
    site.site_name = "Clínica Ejemplo"
    site.save()
    return site.site_name


@pytest.fixture
def logos(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    site_settings = SiteSettings.load()
    site_settings.logo = Image.objects.create(title="Logo", file=get_test_image_file())
    site_settings.footer_logo = Image.objects.create(
        title="Logo claro", file=get_test_image_file(colour="black")
    )
    site_settings.save()
    return site_settings


class TestLogoAndName:
    def test_login_shows_the_logo_and_the_site_name(self, client, site_name, logos):
        html = client.get(reverse("wagtailadmin_login")).content.decode()

        assert re.search(r"<h1[^>]*>[^<]*Clínica Ejemplo[^<]*</h1>", html)
        assert 'class="orion-login-logo"' in html

    def test_without_logo_the_login_keeps_wagtails(self, client, site_name):
        html = client.get(reverse("wagtailadmin_login")).content.decode()

        assert "orion-login-logo" not in html
        assert 'class="login-logo"' in html

    def test_sidebar_shows_the_light_logo(self, admin_client, site_name, logos):
        html = admin_client.get(reverse("wagtailadmin_home")).content.decode()

        assert 'class="orion-sidebar-logo"' in html

    def test_dashboard_and_tab_title_show_the_site_name(self, admin_client, site_name):
        html = admin_client.get(reverse("wagtailadmin_home")).content.decode()

        assert re.search(r"<title>[^<]*Clínica Ejemplo</title>", html)
        assert re.search(r"<h1[^>]*>[^<]*Clínica Ejemplo[^<]*</h1>", html)


class TestColors:
    def test_colors_become_admin_variables(self, client, settings):
        settings.ORION_ADMIN_COLORS = {"primary": "#1d4ed8"}

        response = client.get(reverse("orion_admin_colors"))
        css = response.content.decode()

        assert response["Content-Type"].startswith("text/css")
        hue, saturation, lightness = hex_to_hsl("#1d4ed8")
        assert f"--w-color-primary-hue: {hue};" in css
        assert f"--w-color-primary-saturation: {saturation}%;" in css
        assert f"--w-color-primary-lightness: {lightness}%;" in css

    def test_admin_pages_and_login_load_the_colors(
        self, client, admin_client, settings
    ):
        settings.ORION_ADMIN_COLORS = {"primary": "#1d4ed8"}
        link = f'href="{reverse("orion_admin_colors")}"'

        assert link in client.get(reverse("wagtailadmin_login")).content.decode()
        assert link in admin_client.get(reverse("wagtailadmin_home")).content.decode()

    def test_without_colors_there_is_no_stylesheet(self, admin_client, home_page):
        html = admin_client.get(reverse("wagtailadmin_home")).content.decode()

        assert reverse("orion_admin_colors") not in html

    def test_hsl_conversion(self):
        assert hex_to_hsl("#1d4ed8") == (224, 76, 48)

    @pytest.mark.parametrize(
        ("colors", "message_id"),
        [
            ({"primary": "blue"}, "orion.E004"),
            ({"tertiary": "#1d4ed8"}, "orion.E004"),
            ({"secondary": "#facc15"}, "orion.W001"),
        ],
    )
    def test_checks_report_bad_colors(self, settings, colors, message_id):
        settings.ORION_ADMIN_COLORS = colors

        assert [message.id for message in check_admin_colors(None)] == [message_id]

    def test_readable_colors_pass_the_checks(self, settings):
        settings.ORION_ADMIN_COLORS = {"primary": "#1d4ed8", "secondary": "#15645d"}

        assert check_admin_colors(None) == []
        assert contrast_with_white("#1d4ed8") > 4.5
