import datetime
import re

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail_localize.models import TranslationSource

from orion.core.blocks import ContentStreamBlock
from orion.pages.models import (
    ArticleCategory,
    ArticleIndexPage,
    ArticlePage,
    ArticlePageTag,
    ArticleTag,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def index(home_page):
    page = ArticleIndexPage(title="Novedades", slug="novedades")
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


@pytest.fixture
def health():
    return ArticleCategory.objects.create(name="Salud", slug="salud")


@pytest.fixture
def add_article(index):
    """Create and publish an article in the listing."""

    def _add(title, date=None, categories=(), tags=(), parent=None, **fields):
        article = ArticlePage(
            title=title,
            summary=f"Resumen de {title}",
            date=date or datetime.date(2026, 1, 1),
            categories=list(categories),
            article_tags=[ArticlePageTag(tag=tag) for tag in tags],
            **fields,
        )
        (parent or index).add_child(instance=article)
        article.save_revision().publish()
        return article

    return _add


@pytest.fixture
def english_site(
    home_page, index, english_locale, make_language_public, translate_page
):
    make_language_public(english_locale)
    translate_page(home_page, english_locale)
    translate_page(index, english_locale, slug="news")
    return english_locale


def _titles(html):
    return re.findall(
        r'class="after:absolute after:inset-0 hover:underline">([^<]+)</a>', html
    )


def _sync(page, locale):
    """Create or update a translation like the admin's sync action does."""
    source, _created = TranslationSource.get_or_create_from_instance(page)
    source.update_from_db()
    # wagtail-localize publishes on commit, which tests never reach.
    with TestCase.captureOnCommitCallbacks(execute=True):
        source.create_or_update_translation(locale, fallback=True)
    return page.get_translation(locale).specific


class TestArticle:
    def test_date_defaults_to_today(self):
        assert ArticlePage().date == timezone.localdate()

    def test_image_without_alt_text_is_rejected(self, settings, tmp_path, index):
        settings.MEDIA_ROOT = tmp_path
        image = Image.objects.create(title="Foto", file=get_test_image_file())
        article = ArticlePage(title="Uno", slug="uno", summary="x", image=image)

        with pytest.raises(ValidationError) as error:
            article.clean()
        assert "image_alt" in error.value.message_dict

        article.image_is_decorative = True
        article.clean()

    def test_article_shows_its_classification(self, client, add_article, health):
        tag = ArticleTag.objects.create(name="Prevención", slug="prevencion")
        article = add_article("Uno", categories=[health], tags=[tag])

        html = client.get(article.url).content.decode()

        assert 'href="/novedades/?category=salud"' in html
        assert 'href="/novedades/?tag=prevencion"' in html
        assert re.search(r"<h1\b[^>]*>Uno</h1>", html)

    def test_form_offers_only_categories_of_its_language(
        self, index, health, english_locale
    ):
        health.copy_for_translation(english_locale).save()
        form_class = ArticlePage.get_edit_handler().get_form_class()

        form = form_class(instance=ArticlePage(), parent_page=index, for_user=None)

        assert list(form.fields["categories"].queryset) == [health]

    def test_body_does_not_offer_a_hero(self):
        assert "hero" not in ArticlePage.body.field.stream_block.child_blocks


class TestListing:
    def test_newest_first_and_paginated(self, client, settings, index, add_article):
        settings.ORION_ARTICLES_PER_PAGE = 2
        for day in (1, 3, 2):
            add_article(f"Día {day}", date=datetime.date(2026, 1, day))

        first = client.get("/novedades/").content.decode()
        second = client.get("/novedades/?page=2").content.decode()
        out_of_range = client.get("/novedades/?page=99").content.decode()

        assert _titles(first) == ["Día 3", "Día 2"]
        assert _titles(second) == ["Día 1"]
        assert 'rel="prev"' in second
        assert _titles(out_of_range) == ["Día 1"]

    def test_unpublished_article_is_hidden(self, client, add_article):
        add_article("Visible")
        add_article("Oculto").unpublish()

        assert _titles(client.get("/novedades/").content.decode()) == ["Visible"]

    def test_parent_category_includes_subcategories(self, client, add_article, health):
        prevention = ArticleCategory.objects.create(
            name="Prevención", slug="prevencion", parent=health
        )
        other = ArticleCategory.objects.create(name="Institucional", slug="inst")
        add_article("De salud", categories=[health])
        add_article("De prevención", categories=[prevention])
        add_article("Institucional", categories=[other])

        html = client.get("/novedades/?category=salud").content.decode()

        assert sorted(_titles(html)) == ["De prevención", "De salud"]
        assert re.search(r"<span>[^<]*: Salud</span>", html)
        assert 'href="/novedades/"' in html

    def test_filter_by_tag_keeps_it_in_pagination(self, client, settings, add_article):
        settings.ORION_ARTICLES_PER_PAGE = 1
        tag = ArticleTag.objects.create(name="Vacunas", slug="vacunas")
        add_article("Uno", tags=[tag], date=datetime.date(2026, 1, 1))
        add_article("Dos", tags=[tag], date=datetime.date(2026, 1, 2))
        add_article("Sin etiqueta")

        html = client.get("/novedades/?tag=vacunas").content.decode()

        assert _titles(html) == ["Dos"]
        assert 'href="?tag=vacunas&amp;page=2"' in html

    def test_unknown_filter_is_not_found(self, client, index):
        assert client.get("/novedades/?category=nada").status_code == 404
        assert client.get("/novedades/?tag=nada").status_code == 404

    def test_listing_announces_its_feed(self, client, index):
        html = client.get("/novedades/").content.decode()

        assert (
            '<link rel="alternate" type="application/rss+xml" title="Novedades" '
            'href="/novedades/rss/">' in html
        )


class TestTranslation:
    def test_classification_follows_the_visitor_language(
        self, client, english_site, add_article, health
    ):
        tag = ArticleTag.objects.create(name="Vacunas", slug="vacunas")
        health_en = health.copy_for_translation(english_site)
        health_en.name, health_en.slug = "Health", "health"
        health_en.save()
        article = add_article("Uno", categories=[health], tags=[tag])
        article_en = _sync(article, english_site)

        html = client.get(article_en.url).content.decode()

        assert article_en.url.startswith("/en/news/")
        assert 'href="/en/news/?category=health"' in html
        assert ">Health<" in html
        # Untranslated tags show in the base language.
        assert 'href="/en/news/?tag=vacunas"' in html

        listing = client.get("/en/news/?category=health").content.decode()
        assert _titles(listing) == ["Uno"]

    def test_classification_syncs_to_translations(
        self, english_site, add_article, health
    ):
        article = add_article("Uno", categories=[health])
        _sync(article, english_site)
        news = ArticleCategory.objects.create(name="Noticias", slug="noticias")
        article.categories = [health, news]
        article.save_revision().publish()

        article_en = _sync(article, english_site)

        assert set(article_en.categories.all()) == {health, news}

    def test_feed_in_english(self, client, english_site, add_article):
        article_en = _sync(add_article("Uno"), english_site)

        response = client.get("/en/news/rss/")
        feed = response.content.decode()

        assert response["Content-Type"].startswith("application/rss+xml")
        assert f"<link>http://testserver{article_en.url}</link>" in feed
        assert "<description>Resumen de Uno</description>" in feed
        assert "/novedades/" not in feed


class TestLatestArticles:
    @staticmethod
    def _home_with_block(home_page, **value):
        stream_block = ContentStreamBlock()
        raw = [{"type": "latest_articles", "value": value}]
        home_page.body = stream_block.clean(stream_block.to_python(raw))
        home_page.save_revision().publish()

    def test_shows_the_most_recent(self, client, home_page, add_article):
        for day in range(1, 6):
            add_article(f"Día {day}", date=datetime.date(2026, 1, day))
        self._home_with_block(home_page, count=3)

        html = client.get("/").content.decode()

        assert _titles(html) == ["Día 5", "Día 4", "Día 3"]

    def test_chosen_listing_in_another_language(
        self, client, home_page, english_site, index, add_article
    ):
        _sync(add_article("Uno"), english_site)
        self._home_with_block(home_page, count=3, index=index.pk)
        _sync(home_page, english_site)

        html = client.get("/en/").content.decode()

        assert len(_titles(html)) == 1
        assert 'href="/en/news/uno/"' in html

    def test_without_articles_nothing_is_shown(self, client, home_page, index):
        self._home_with_block(home_page, title="<p>Novedades</p>")

        html = client.get("/").content.decode()

        assert "block-latest_articles" not in html


class TestArticleImages:
    def test_article_image_is_main_and_card_image_is_lazy(
        self, settings, tmp_path, client, index, add_article
    ):
        settings.MEDIA_ROOT = tmp_path
        image = Image.objects.create(
            title="Foto", file=get_test_image_file(size=(1600, 900))
        )
        article = add_article("Uno", image=image, image_alt="Una foto")

        article_html = client.get(article.url).content.decode()
        listing_html = client.get(index.url).content.decode()

        article_img = article_html.split("<picture>", 1)[1].split("<img", 1)[1]
        card_img = listing_html.split("<picture>", 1)[1].split("<img", 1)[1]
        assert 'fetchpriority="high"' in article_img.split(">", 1)[0]
        assert 'alt="Una foto"' in article_img.split(">", 1)[0]
        assert 'loading="lazy"' in card_img.split(">", 1)[0]
        assert 'type="image/avif"' in listing_html
