import pytest
from wagtail.models import Locale

pytestmark = pytest.mark.django_db


@pytest.fixture
def public_english(english_locale, make_language_public):
    make_language_public(english_locale)
    return english_locale


class TestPrefixes:
    def test_base_language_page_has_no_prefix(self, client, services_page):
        response = client.get("/servicios/")

        assert response.status_code == 200
        assert '<html lang="es"' in response.content.decode()

    def test_secondary_language_page_uses_its_prefix(
        self, client, home_page, services_page, public_english, translate_page
    ):
        translate_page(home_page, public_english)
        translate_page(services_page, public_english, slug="services")

        response = client.get("/en/services/")

        assert response.status_code == 200
        assert '<html lang="en"' in response.content.decode()

    def test_prefixed_url_ignores_browser_language(
        self, client, home_page, public_english, translate_page
    ):
        translate_page(home_page, public_english)

        response = client.get("/en/", HTTP_ACCEPT_LANGUAGE="es")

        assert '<html lang="en"' in response.content.decode()


class TestRedirects:
    def test_non_public_language_redirects_to_base_home(
        self, client, home_page, english_locale, translate_page
    ):
        translate_page(home_page, english_locale)

        response = client.get("/en/")

        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_untranslated_page_redirects_to_language_home(
        self, client, home_page, services_page, public_english, translate_page
    ):
        translate_page(home_page, public_english)

        response = client.get("/en/servicios/")

        assert response.status_code == 302
        assert response["Location"] == "/en/"

    def test_language_without_published_home_redirects_to_base_home(
        self, client, home_page, services_page, public_english, translate_page
    ):
        translate_page(home_page, public_english, publish=False)

        response = client.get("/en/servicios/")

        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_base_language_content_is_never_served_under_a_prefix(
        self, client, services_page, public_english
    ):
        # Without an English home, Wagtail falls back to the base language's tree.
        response = client.get("/en/servicios/")

        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_base_language_missing_page_is_a_plain_404(self, client, home_page):
        assert client.get("/no-existe/").status_code == 404

    def test_post_is_not_redirected(self, client, public_english):
        assert client.post("/en/no-existe/").status_code != 302


class TestLanguageSwitcher:
    def test_hidden_with_a_single_public_language(self, client, home_page):
        assert "language-switcher" not in client.get("/").content.decode()

    def test_links_to_the_translation(
        self, client, home_page, services_page, public_english, translate_page
    ):
        translate_page(home_page, public_english)
        translate_page(services_page, public_english, slug="services")

        html = client.get("/servicios/").content.decode()

        assert 'href="/en/services/"' in html
        assert 'href="/servicios/" hreflang="es" lang="es" aria-current="true"' in html

    def test_links_to_language_home_when_untranslated(
        self, client, home_page, services_page, public_english, translate_page
    ):
        translate_page(home_page, public_english)

        html = client.get("/servicios/").content.decode()

        assert 'href="/en/" hreflang="en"' in html

    def test_hides_non_public_languages(
        self, client, home_page, public_english, translate_page
    ):
        Locale.objects.create(language_code="fr")
        translate_page(home_page, public_english)

        html = client.get("/").content.decode()

        assert 'hreflang="en"' in html
        assert 'hreflang="fr"' not in html


class TestHreflang:
    def test_both_versions_declare_each_other(
        self, client, home_page, services_page, public_english, translate_page
    ):
        translate_page(home_page, public_english)
        translate_page(services_page, public_english, slug="services")

        for url in ("/servicios/", "/en/services/"):
            html = client.get(url).content.decode()
            assert '<link rel="alternate" hreflang="es" href="http' in html
            assert '<link rel="alternate" hreflang="en" href="http' in html
            assert 'hreflang="x-default" href="http' in html
            assert "/servicios/" in html.split('hreflang="x-default"')[1][:80]

    def test_translations_in_non_public_languages_are_not_declared(
        self, client, home_page, services_page, english_locale, translate_page
    ):
        translate_page(home_page, english_locale)
        translate_page(services_page, english_locale, slug="services")

        html = client.get("/servicios/").content.decode()

        assert 'rel="alternate"' not in html
