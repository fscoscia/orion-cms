import pytest
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils import translation
from wagtail.blocks import StructBlockValidationError

from orion.core.blocks import LinkBlock, normalize_phone

pytestmark = pytest.mark.django_db


def _clean(block, **data):
    return block.clean(block.to_python(data))


class TestDestinations:
    @pytest.fixture(autouse=True)
    def _english_messages(self):
        # The base language is Spanish; check the source messages.
        with translation.override("en"):
            yield

    def test_two_destinations_are_rejected(self, services_page):
        with pytest.raises(StructBlockValidationError) as error:
            _clean(LinkBlock(), page=services_page.pk, url="https://example.org/")

        assert "only one destination" in str(error.value.non_block_errors)

    def test_a_destination_is_required_by_default(self):
        with pytest.raises(StructBlockValidationError) as error:
            _clean(LinkBlock(), label="Sin destino")

        assert "Choose a destination" in str(error.value.non_block_errors)

    def test_label_only_is_allowed_when_destination_is_optional(self):
        value = _clean(LinkBlock(require_destination=False), label="Institucional")

        assert value.is_visible is False

    def test_own_site_url_is_rejected(self):
        with pytest.raises(ValidationError):
            _clean(LinkBlock(), url="http://localhost/servicios/")

    def test_invalid_phone_is_rejected(self):
        with pytest.raises(ValidationError):
            _clean(LinkBlock(), phone="llamanos")


class TestResolution:
    def test_page_link_follows_the_active_language(
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
        value = LinkBlock().to_python({"page": services_page.pk})

        with translation.override("en"):
            assert value.href == "/en/services/"

    def test_page_link_falls_back_to_the_chosen_page(self, services_page):
        value = LinkBlock().to_python({"page": services_page.pk})

        with translation.override("en"):
            assert value.href == "/servicios/"

    def test_unpublished_page_hides_the_link(self, services_page):
        services_page.unpublish()
        value = LinkBlock().to_python({"page": services_page.pk})

        assert value.is_visible is False

    def test_text_defaults_to_the_page_title(self, services_page):
        value = LinkBlock().to_python({"page": services_page.pk})

        assert value.text == "Servicios"

    def test_email_and_phone_links(self):
        email = LinkBlock().to_python({"email": "hola@example.com"})
        phone = LinkBlock().to_python({"phone": "+595 21 729 1444"})

        assert email.href == "mailto:hola@example.com"
        assert phone.href == "tel:+595217291444"
        assert phone.text == "+595 21 729 1444"

    def test_phone_normalization_without_plus(self):
        assert normalize_phone("(021) 729-1444") == "0217291444"


class TestRendering:
    def test_external_link_in_new_tab_is_safe(self):
        value = LinkBlock().to_python(
            {"url": "https://example.org/", "label": "Ejemplo", "open_in_new_tab": True}
        )

        html = render_to_string("orion/includes/link.html", {"link": value})

        assert 'target="_blank"' in html
        assert 'rel="noopener noreferrer"' in html

    def test_new_tab_is_ignored_for_internal_pages(self, services_page):
        value = LinkBlock().to_python(
            {"page": services_page.pk, "open_in_new_tab": True}
        )

        html = render_to_string("orion/includes/link.html", {"link": value})

        assert "target=" not in html
