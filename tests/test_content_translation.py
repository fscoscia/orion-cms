import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from wagtail.models import Page
from wagtail_localize.models import (
    StringSegment,
    StringTranslation,
    Translation,
    TranslationSource,
)

pytestmark = pytest.mark.django_db


def _start_translation(page, locale):
    source, _created = TranslationSource.get_or_create_from_instance(page)
    translation = Translation.objects.create(source=source, target_locale=locale)
    translation.save_target(publish=False)
    return translation


def _translate_all_segments(translation, text_prefix):
    for segment in StringSegment.objects.filter(source=translation.source):
        StringTranslation.objects.update_or_create(
            translation_of=segment.string,
            locale=translation.target_locale,
            context=segment.context,
            defaults={"data": f"{text_prefix} {segment.string.data}"},
        )


class TestCreateTranslation:
    def test_translation_starts_as_a_linked_draft(self, services_page, english_locale):
        _start_translation(services_page, english_locale)

        translated_page = services_page.get_translation(english_locale)

        assert translated_page.live is False
        assert translated_page.translation_key == services_page.translation_key

    def test_translation_lists_every_text_to_translate(
        self, services_page, english_locale
    ):
        translation = _start_translation(services_page, english_locale)

        total_segments, translated_segments = translation.get_progress()

        assert total_segments > 0
        assert translated_segments == 0

    def test_editors_can_open_the_translate_action(
        self, client, django_user_model, services_page, english_locale
    ):
        editor = django_user_model.objects.create_user("editor", password="x")
        editor.groups.add(Group.objects.get(name="Editores"))
        client.force_login(editor)

        response = client.get(
            reverse("wagtail_localize:submit_page_translation", args=[services_page.pk])
        )

        assert response.status_code == 200

    def test_users_without_translate_permission_are_rejected(
        self, client, django_user_model, services_page, english_locale
    ):
        user = django_user_model.objects.create_user("viewer", password="x")
        user.user_permissions.add(Permission.objects.get(codename="access_admin"))
        client.force_login(user)

        response = client.post(
            reverse(
                "wagtail_localize:submit_page_translation", args=[services_page.pk]
            ),
            {"locales": [english_locale.pk]},
        )

        assert response.status_code in {302, 403}
        assert services_page.get_translation_or_none(english_locale) is None


class TestOutdatedTranslation:
    def test_changed_original_marks_texts_pending_without_publishing(
        self, services_page, english_locale
    ):
        translation = _start_translation(services_page, english_locale)
        _translate_all_segments(translation, "EN")
        translation.save_target(publish=True)
        published_title = services_page.get_translation(english_locale).title

        services_page.title = "Servicios y precios"
        services_page.save_revision().publish()
        translation.source.update_from_db()

        total_segments, translated_segments = translation.get_progress()
        translated_page = Page.objects.get(
            pk=services_page.get_translation(english_locale).pk
        )
        assert translated_segments < total_segments
        assert translated_page.title == published_title
