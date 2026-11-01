import re
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

import orion
from orion.navigation.models import Menu, MenuLocation
from orion.site_data.models import SiteSettings, SiteTexts

pytestmark = pytest.mark.django_db

ORION_DIR = Path(orion.__file__).parent
COMPILED_CSS = ORION_DIR / "core" / "static" / "orion" / "css" / "orion.css"
# Plain class attributes and include arguments, not Alpine's x-bind:class.
CLASS_ATTRIBUTE = re.compile(r'(?<![\w:-])class(?:_name)?="([^"]*)"')
TEMPLATE_TAG = re.compile(r"{%.*?%}|{{.*?}}")


@pytest.fixture
def site_with_name(home_page):
    site = Site.objects.get(is_default_site=True)
    site.site_name = "Clínica Ejemplo"
    site.save()
    return site


@pytest.fixture
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def _home_html(client):
    return client.get("/").content.decode()


class TestStructure:
    def test_skip_link_is_the_first_focusable_element(self, client, home_page):
        body = _home_html(client).split("<body", 1)[1]

        first_focusable = re.search(r"<(a|button)\b[^>]*>", body).group()

        assert 'href="#main-content"' in first_focusable
        assert 'id="main-content"' in body

    def test_page_with_all_data_loaded(self, client, site_with_name, services_page):
        site_settings = SiteSettings.load()
        site_settings.phone = "+595 21 729 1444"
        site_settings.email = "hola@example.com"
        site_settings.address = "Av. Siempre Viva 742"
        site_settings.social_links = [
            {
                "type": "social_link",
                "value": {"network": "instagram", "url": "https://instagram.com/x"},
            }
        ]
        site_settings.save()
        SiteTexts.objects.create(tagline="Cuidamos de vos", legal_text="© Ejemplo")
        for location in (MenuLocation.HEADER, MenuLocation.FOOTER):
            Menu.objects.create(
                location=location,
                items=[
                    {
                        "type": "item",
                        "value": {
                            "link": {
                                "label": f"Ir {location}",
                                "page": services_page.pk,
                            },
                            "subitems": [],
                        },
                    }
                ],
            )

        html = _home_html(client)
        header = html.split("<header", 1)[1].split("</header>", 1)[0]
        footer = html.split("<footer", 1)[1].split("</footer>", 1)[0]

        assert "Clínica Ejemplo" in header
        assert "Ir header" in header
        assert "Cuidamos de vos" in footer
        assert 'href="tel:+595217291444"' in footer
        assert 'href="mailto:hola@example.com"' in footer
        assert "Av. Siempre Viva 742" in footer
        assert 'href="https://instagram.com/x"' in footer
        assert '<span class="sr-only">Instagram</span>' in footer
        assert "Ir footer" in footer
        assert "© Ejemplo" in footer

    def test_missing_data_leaves_no_empty_markers(self, client, home_page):
        footer = _home_html(client).split("<footer", 1)[1].split("</footer>", 1)[0]

        assert "<address" not in footer
        assert "Social networks" not in footer
        assert "<nav" not in footer


class TestLogo:
    def test_without_logo_the_site_name_links_home(self, client, site_with_name):
        html = _home_html(client)

        brand = re.search(
            r'<a href="/" class="site-header__brand[^>]*>(.*?)</a>', html, re.S
        )

        assert brand.group(1).strip() == "Clínica Ejemplo"

    def test_logo_replaces_the_name_and_keeps_it_accessible(
        self, client, site_with_name, media_root
    ):
        site_settings = SiteSettings.load()
        site_settings.logo = Image.objects.create(
            title="Logo", file=get_test_image_file()
        )
        site_settings.save()

        html = _home_html(client)
        brand = re.search(r'class="site-header__brand[^>]*>(.*?)</a>', html, re.S)

        assert "<img" in brand.group(1)
        assert '<span class="sr-only">Clínica Ejemplo</span>' in brand.group(1)


class TestStyles:
    def test_pages_load_orion_stylesheet(self, client, home_page):
        html = _home_html(client)

        assert 'rel="stylesheet" href="/static/orion/css/orion.css"' in html
        assert finders.find("orion/css/orion.css")

    def test_scripts_are_external_and_deferred(self, client, home_page):
        scripts = re.findall(r"<script\b[^>]*>", _home_html(client))
        # JSON-LD is data: browsers do not run it, so a strict CSP allows it inline.
        code = [tag for tag in scripts if "application/ld+json" not in tag]

        assert code
        assert all("src=" in tag and "defer" in tag for tag in code)

    def test_theme_is_exposed_as_css_variables(self):
        css = COMPILED_CSS.read_text()

        for variable in ("--color-primary-700", "--color-accent-500", "--font-sans"):
            assert f"{variable}:" in css

    def test_compiled_css_has_the_classes_of_orion_templates(self):
        """Fails when a template changes and `pipenv run css-build` was not run."""
        css = COMPILED_CSS.read_text()
        classes = set()
        for template in ORION_DIR.glob("*/templates/**/*.html"):
            source = template.read_text()
            # Admin templates use Wagtail's admin styles, not Orion's stylesheet.
            is_admin = (
                template.parent.name == "widgets"
                or "editor" in template.parts
                or "integrations" in template.parts
                or '{% extends "wagtailadmin/' in source
            )
            if is_admin:
                continue
            for attribute in CLASS_ATTRIBUTE.findall(source):
                classes.update(TEMPLATE_TAG.sub(" ", attribute).split())
        # Hooks, components and state classes are Orion's own, not Tailwind utilities.
        own_prefixes = ("site-", "is-", "language-", "orion-", "block-")
        utilities = {
            name
            for name in classes
            if "__" not in name and not name.startswith(own_prefixes)
        }

        missing = {
            name
            for name in utilities
            if "." + re.sub(r"([^a-zA-Z0-9_-])", r"\\\1", name) not in css
        }

        assert utilities
        assert not missing, f"Run `pipenv run css-build`; missing: {sorted(missing)}"
