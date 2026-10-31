import datetime
import json
import re

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file, get_test_image_file_svg
from wagtail.models import Locale, Site

from orion.core.blocks import ContentStreamBlock
from orion.pages.models import ArticleIndexPage, ArticlePage, ContentPage
from orion.site_data.models import SiteSettings, SiteTexts

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def site(settings, tmp_path, home_page):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.get(is_default_site=True)
    site.site_name = "Clínica Ejemplo"
    site.hostname, site.port = "testserver", 80
    site.save()
    return site


@pytest.fixture
def image():
    return Image.objects.create(
        title="Foto", file=get_test_image_file(size=(1600, 900))
    )


def _page(parent, title, slug, page_class=ContentPage, **fields):
    page = page_class(title=title, slug=slug, **fields)
    parent.add_child(instance=page)
    page.save_revision().publish()
    return page


def _hero(image):
    stream_block = ContentStreamBlock()
    raw = [
        {
            "type": "hero",
            "value": {
                "title": "<p>T</p>",
                "image": {"image": image.pk, "alt_text": "x", "decorative": False},
            },
        }
    ]
    return stream_block.clean(stream_block.to_python(raw))


def _head(client, url):
    return client.get(url).content.decode().split("</head>", 1)[0]


def _meta(head, attribute, name):
    match = re.search(rf'<meta {attribute}="{re.escape(name)}" content="([^"]*)"', head)
    return match.group(1) if match else None


def _canonical(head):
    return re.search(r'<link rel="canonical" href="([^"]*)"', head).group(1)


def _json_ld(html):
    data = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    ).group(1)
    return {item["@type"]: item for item in json.loads(data)["@graph"]}


@pytest.fixture
def site_texts():
    return SiteTexts.objects.create(
        locale=Locale.get_default(), description="Salud cerca tuyo."
    )


class TestTitleAndDescription:
    def test_fallbacks(self, client, home_page, site_texts):
        page = _page(home_page, "Servicios", "servicios")

        head = _head(client, page.url)

        assert "<title>Servicios | Clínica Ejemplo</title>" in head
        assert _meta(head, "name", "description") == "Salud cerca tuyo."

    def test_seo_title_is_used_as_is(self, client, home_page):
        page = _page(
            home_page,
            "Servicios",
            "servicios",
            seo_title="Turnos online en Asunción",
            search_description="Pedí tu turno.",
        )

        head = _head(client, page.url)

        assert "<title>Turnos online en Asunción</title>" in head
        assert _meta(head, "name", "description") == "Pedí tu turno."

    def test_site_name_is_not_repeated(self, client, home_page):
        page = _page(home_page, "Clínica Ejemplo", "clinica")

        assert "<title>Clínica Ejemplo</title>" in _head(client, page.url)

    def test_without_description(self, client, home_page):
        page = _page(home_page, "Servicios", "servicios")

        assert 'name="description"' not in _head(client, page.url)


class TestCanonical:
    def test_query_string_is_dropped(self, client, home_page):
        page = _page(home_page, "Servicios", "servicios")

        head = _head(client, f"{page.url}?utm_source=x")

        assert _canonical(head) == "http://testserver/servicios/"

    def test_listing_page_number(self, client, settings, home_page):
        settings.ORION_ARTICLES_PER_PAGE = 1
        index = _page(home_page, "Novedades", "novedades", ArticleIndexPage)
        for number in (1, 2):
            _page(index, f"Nota {number}", f"nota-{number}", ArticlePage, summary="x")

        first = _canonical(_head(client, index.url))
        second = _canonical(_head(client, f"{index.url}?page=2&utm=x"))

        assert first == "http://testserver/novedades/"
        assert second == "http://testserver/novedades/?page=2"


class TestRobotsMeta:
    def test_no_index_and_no_follow(self, client, home_page):
        page = _page(home_page, "Gracias", "gracias", no_index=True, no_follow=True)

        assert _meta(_head(client, page.url), "name", "robots") == "noindex, nofollow"

    def test_indexed_by_default(self, client, home_page):
        page = _page(home_page, "Servicios", "servicios")

        assert 'name="robots"' not in _head(client, page.url)

    def test_fields_in_the_promote_tab(self, admin_client, home_page):
        page = _page(home_page, "Servicios", "servicios")

        html = admin_client.get(
            reverse("wagtailadmin_pages:edit", args=[page.pk])
        ).content.decode()

        for field in ("social_image", "no_index", "no_follow"):
            assert f'name="{field}"' in html


class TestSocialNetworks:
    def test_article_uses_its_image(self, client, home_page, image):
        index = _page(home_page, "Novedades", "novedades", ArticleIndexPage)
        article = _page(
            index, "Nota", "nota", ArticlePage, summary="x", image=image, image_alt="x"
        )

        head = _head(client, article.url)

        assert _meta(head, "property", "og:type") == "article"
        assert "fill-1200x630" in _meta(head, "property", "og:image")
        assert _meta(head, "property", "og:image").startswith("http://testserver/")
        assert _meta(head, "name", "twitter:card") == "summary_large_image"

    def test_page_starting_with_a_hero_uses_its_image(self, client, home_page, image):
        page = _page(home_page, "Servicios", "servicios", body=_hero(image))

        og_image = _meta(_head(client, page.url), "property", "og:image")

        assert "fill-1200x630" in og_image

    def test_site_default_image(self, client, home_page, image):
        site_settings = SiteSettings.load()
        site_settings.social_image = image
        site_settings.save()
        page = _page(home_page, "Servicios", "servicios")

        head = _head(client, page.url)

        assert "fill-1200x630" in _meta(head, "property", "og:image")
        assert _meta(head, "property", "og:url") == "http://testserver/servicios/"
        assert _meta(head, "property", "og:site_name") == "Clínica Ejemplo"
        assert _meta(head, "property", "og:locale") == "es"

    def test_without_images(self, client, home_page):
        page = _page(home_page, "Servicios", "servicios")

        head = _head(client, page.url)

        assert 'property="og:image"' not in head
        assert _meta(head, "name", "twitter:card") == "summary"


class TestSiteSettings:
    def test_search_console_code(self, client, home_page):
        site_settings = SiteSettings.load()
        site_settings.google_site_verification = "abc_DEF-123"
        site_settings.save()

        head = _head(client, home_page.url)

        assert _meta(head, "name", "google-site-verification") == "abc_DEF-123"

    def test_pasted_tag_is_rejected(self):
        site_settings = SiteSettings.load()
        site_settings.google_site_verification = (
            '<meta name="google-site-verification" content="abc" />'
        )

        with pytest.raises(ValidationError) as error:
            site_settings.full_clean()

        assert "google_site_verification" in error.value.message_dict

    def test_seo_tab(self, admin_client):
        url = reverse(
            "wagtailsettings:edit",
            args=["orion_site_data", "sitesettings", SiteSettings.load().pk],
        )

        html = admin_client.get(url).content.decode()

        for field in (
            "favicon",
            "social_image",
            "robots_txt",
            "google_site_verification",
        ):
            assert f'name="{field}"' in html

    def test_favicon_links(self, client, home_page, image):
        site_settings = SiteSettings.load()
        site_settings.favicon = image
        site_settings.save()

        head = _head(client, home_page.url)

        for sizes in ("32x32", "192x192"):
            assert re.search(
                rf'<link rel="icon" type="image/png" sizes="{sizes}"', head
            )
        assert 'rel="apple-touch-icon" sizes="180x180"' in head


class TestStructuredData:
    def test_article(self, client, home_page, image):
        site_settings = SiteSettings.load()
        site_settings.logo = image
        site_settings.phone = "+595 21 000 000"
        site_settings.save()
        index = _page(home_page, "Novedades", "novedades", ArticleIndexPage)
        article = _page(
            index,
            "Nota",
            "nota",
            ArticlePage,
            summary="Resumen",
            date=datetime.date(2026, 10, 1),
        )

        graph = _json_ld(client.get(article.url).content.decode())

        assert graph["WebSite"]["name"] == "Clínica Ejemplo"
        assert graph["Organization"]["telephone"] == "+595 21 000 000"
        assert graph["Organization"]["logo"].startswith("http://testserver/")
        assert "email" not in graph["Organization"]
        assert [
            item["name"] for item in graph["BreadcrumbList"]["itemListElement"]
        ] == [
            home_page.title,
            "Novedades",
            "Nota",
        ]
        assert graph["Article"]["headline"] == "Nota"
        assert graph["Article"]["datePublished"] == "2026-10-01"
        assert graph["Article"]["description"] == "Resumen"
        head = _head(client, article.url)
        assert _meta(head, "name", "description") == "Resumen"

    def test_home_has_no_breadcrumbs(self, client, home_page):
        graph = _json_ld(client.get(home_page.url).content.decode())

        assert "BreadcrumbList" not in graph

    def test_markup_cannot_close_the_script(self, client, home_page):
        page = _page(home_page, "Hola</script><script>alert(1)", "hola")

        html = client.get(page.url).content.decode()

        assert "</script><script>alert(1)" not in html
        assert _json_ld(html)["BreadcrumbList"]["itemListElement"][-1]["name"] == (
            "Hola</script><script>alert(1)"
        )


class TestSitemap:
    def test_public_languages_only(
        self, client, home_page, english_locale, make_language_public, translate_page
    ):
        page = _page(home_page, "Servicios", "servicios")
        french = Locale.objects.create(language_code="fr")
        make_language_public(english_locale)
        translate_page(home_page, english_locale)
        translate_page(page, english_locale, slug="services")
        translate_page(home_page, french)
        translate_page(page, french, slug="services-fr")

        xml = client.get("/sitemap.xml").content.decode()

        assert "http://testserver/servicios/" in xml
        assert "http://testserver/en/services/" in xml
        assert "services-fr" not in xml

    def test_excludes_no_index_private_and_drafts(self, client, home_page):
        _page(home_page, "Servicios", "servicios")
        _page(home_page, "Gracias", "gracias", no_index=True)
        draft = ContentPage(title="Borrador", slug="borrador", live=False)
        home_page.add_child(instance=draft)

        xml = client.get("/sitemap.xml").content.decode()

        assert "/gracias/" not in xml
        assert "/borrador/" not in xml
        assert re.search(r"<loc>http://testserver/servicios/</loc><lastmod>", xml)


class TestRobotsTxt:
    def test_default(self, client, settings):
        text = client.get("/robots.txt").content.decode()

        assert "User-agent: *" in text
        assert f"Disallow: /{settings.ORION_ADMIN_PATH}" in text
        assert "Sitemap: http://testserver/sitemap.xml" in text

    def test_custom_text_gets_the_sitemap(self, client):
        site_settings = SiteSettings.load()
        site_settings.robots_txt = "User-agent: *\r\nDisallow: /privado/"
        site_settings.save()

        response = client.get("/robots.txt")

        assert response["Content-Type"].startswith("text/plain")
        assert response.content.decode() == (
            "User-agent: *\nDisallow: /privado/\n"
            "Sitemap: http://testserver/sitemap.xml\n"
        )


class TestFaviconIco:
    def test_without_favicon(self, client):
        assert client.get("/favicon.ico").status_code == 404

    def test_png(self, client, image):
        site_settings = SiteSettings.load()
        site_settings.favicon = image
        site_settings.save()

        response = client.get("/favicon.ico")

        assert response.status_code == 302
        assert "fill-32x32" in response["Location"]

    def test_svg(self, client):
        site_settings = SiteSettings.load()
        site_settings.favicon = Image.objects.create(
            title="Ícono", file=get_test_image_file_svg()
        )
        site_settings.save()

        assert client.get("/favicon.ico")["Location"].endswith(".svg")
