import pytest
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from wagtail.coreutils import get_content_languages
from wagtail.models import Locale
from wagtail_localize.locales.forms import LocaleForm

from orion.localization.languages import get_public_language_codes
from orion.localization.models import LanguageSettings

pytestmark = pytest.mark.django_db


def _language_settings_url():
    # Generic settings are edited at a URL that includes the settings object's id.
    return reverse(
        "wagtailsettings:edit",
        args=["orion_localization", "languagesettings", LanguageSettings.load().pk],
    )


class TestCatalog:
    def test_content_languages_are_the_catalog(self):
        assert list(get_content_languages()) == [
            code for code, _name in settings.LANGUAGES
        ]

    def test_language_form_only_offers_catalog_languages(self):
        offered = {code for code, _name in LocaleForm().fields["language_code"].choices}

        assert offered
        assert offered <= set(dict(settings.LANGUAGES))


class TestBaseLanguage:
    def test_new_site_has_only_the_base_language(self):
        assert list(Locale.objects.values_list("language_code", flat=True)) == ["es"]

    def test_base_language_is_public_even_if_not_marked(self):
        assert LanguageSettings.load().public_locales.count() == 0
        assert get_public_language_codes() == {"es"}


class TestPublicLanguages:
    def test_added_language_is_not_public(self, english_locale):
        assert get_public_language_codes() == {"es"}

    def test_marked_language_is_public(self, english_locale, make_language_public):
        make_language_public(english_locale)

        assert get_public_language_codes() == {"es", "en"}


class TestPermissions:
    def test_editor_cannot_change_public_languages(self, client, django_user_model):
        editor = django_user_model.objects.create_user("editor", password="x")
        editor.groups.add(Group.objects.get(name="Editors"))
        client.force_login(editor)

        response = client.get(_language_settings_url())

        assert response.status_code in {302, 403}
        assert response.status_code != 200

    def test_user_with_permission_can_change_public_languages(
        self, client, django_user_model, english_locale
    ):
        manager = django_user_model.objects.create_user("manager", password="x")
        manager.user_permissions.add(
            Permission.objects.get(codename="access_admin"),
            Permission.objects.get(codename="change_languagesettings"),
        )
        client.force_login(manager)

        response = client.post(
            _language_settings_url(), {"public_locales": [english_locale.pk]}
        )

        assert response.status_code == 302
        assert get_public_language_codes() == {"es", "en"}
