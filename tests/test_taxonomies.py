import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import reverse
from wagtail.models import Locale

from orion.pages.models import ArticleCategory, ArticleTag

pytestmark = pytest.mark.django_db


@pytest.fixture
def health():
    return ArticleCategory.objects.create(name="Salud", slug="salud")


class TestCategories:
    def test_two_levels_are_allowed(self, health):
        prevention = ArticleCategory(
            name="Prevención", parent=health, locale=Locale.get_default()
        )

        prevention.full_clean()

    def test_third_level_is_rejected(self, health):
        prevention = ArticleCategory.objects.create(name="Prevención", parent=health)
        vaccines = ArticleCategory(
            name="Vacunas", parent=prevention, locale=Locale.get_default()
        )

        with pytest.raises(ValidationError):
            vaccines.full_clean()

    def test_category_with_children_cannot_get_a_parent(self, health):
        ArticleCategory.objects.create(name="Prevención", parent=health)
        news = ArticleCategory.objects.create(name="Noticias", slug="noticias")
        health.parent = news

        with pytest.raises(ValidationError):
            health.full_clean()

    def test_slug_is_built_from_the_name(self):
        category = ArticleCategory(name="Salud Mental", locale=Locale.get_default())

        category.full_clean()

        assert category.slug == "salud-mental"

    def test_repeated_slug_in_a_language_is_rejected(self, health):
        duplicate = ArticleCategory(
            name="Salud 2", slug="salud", locale=Locale.get_default()
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_same_slug_in_another_language_is_allowed(self, health, english_locale):
        english = ArticleCategory(name="Salud", slug="salud", locale=english_locale)

        english.full_clean()


class TestEditingRights:
    def test_editors_can_create_tags_and_categories(self, client, django_user_model):
        editor = django_user_model.objects.create_user("editor", password="x")
        editor.groups.add(Group.objects.get(name="Editors"))
        client.force_login(editor)

        for model_name in ("articletag", "articlecategory"):
            assert editor.has_perm(f"orion_pages.add_{model_name}")
            assert editor.has_perm(f"orion_pages.change_{model_name}")
            response = client.get(
                reverse(f"wagtailsnippets_orion_pages_{model_name}:add")
            )
            assert response.status_code == 200

    def test_tag_is_saved(self):
        tag = ArticleTag(name="Prevención", locale=Locale.get_default())
        tag.full_clean()
        tag.save()

        assert ArticleTag.objects.get(slug="prevencion").name == "Prevención"

    def test_name_without_latin_letters_gets_a_valid_slug(self):
        tag = ArticleTag(name="Здоровье", locale=Locale.get_default())

        tag.full_clean()

        assert tag.slug
        assert tag.slug.isascii()

    def test_slug_with_accents_is_rejected(self):
        tag = ArticleTag(name="Salud", slug="salúd", locale=Locale.get_default())

        with pytest.raises(ValidationError):
            tag.full_clean()
