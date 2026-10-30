import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import translation
from wagtail.models import Locale

from orion.site_data.models import SiteSettings, SiteTexts, SocialLinkBlock

pytestmark = pytest.mark.django_db


def _login_editor(client, django_user_model):
    editor = django_user_model.objects.create_user("editor", password="x")
    editor.groups.add(Group.objects.get(name="Editors"))
    client.force_login(editor)
    return editor


class TestFixedData:
    def test_contact_data_is_shared_by_every_language(
        self,
        client,
        home_page,
        english_locale,
        make_language_public,
        translate_page,
    ):
        site_settings = SiteSettings.load()
        site_settings.phone = "+595 21 729 1444"
        site_settings.save()
        make_language_public(english_locale)
        translate_page(home_page, english_locale)

        for url in ("/", "/en/"):
            assert "+595 21 729 1444" in client.get(url).content.decode()

    def test_social_network_requires_a_valid_url(self):
        block = SocialLinkBlock()

        with pytest.raises(ValidationError):
            block.clean(block.to_python({"network": "instagram", "url": "no es url"}))


class TestTranslatableTexts:
    def test_falls_back_to_the_base_language(self, english_locale):
        SiteTexts.objects.create(legal_text="Todos los derechos reservados")

        with translation.override("en"):
            texts = SiteTexts.for_active_language()

        assert texts.legal_text == "Todos los derechos reservados"

    def test_uses_the_translation_when_it_exists(self, english_locale):
        base_texts = SiteTexts.objects.create(legal_text="Derechos reservados")
        english_texts = base_texts.copy_for_translation(english_locale)
        english_texts.legal_text = "All rights reserved"
        english_texts.save()

        with translation.override("en"):
            assert SiteTexts.for_active_language().legal_text == "All rights reserved"

    def test_only_one_version_per_language(self):
        SiteTexts.objects.create(tagline="Primero")
        # The admin sets the locale before validating; Wagtail only defaults it on save.
        duplicate = SiteTexts(tagline="Segundo", locale=Locale.get_default())

        with pytest.raises(ValidationError):
            duplicate.full_clean()


class TestEditingRights:
    def test_editors_can_edit_site_texts(self, client, django_user_model):
        texts = SiteTexts.objects.create(tagline="Hola")
        _login_editor(client, django_user_model)

        response = client.get(
            reverse("wagtailsnippets_orion_site_data_sitetexts:edit", args=[texts.pk])
        )

        assert response.status_code == 200

    def test_editors_cannot_open_fixed_site_data(self, client, django_user_model):
        _login_editor(client, django_user_model)

        response = client.get(
            reverse(
                "wagtailsettings:edit",
                args=["orion_site_data", "sitesettings", SiteSettings.load().pk],
            )
        )

        assert response.status_code != 200
