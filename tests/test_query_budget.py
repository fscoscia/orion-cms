"""Queries per page type, without the page cache. They must not grow with the number
of blocks, images or articles shown; raise a budget only for a deliberate change."""

import datetime

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from orion.core.blocks import ContentStreamBlock
from orion.pages.models import ArticleIndexPage, ArticlePage, ContentPage

pytestmark = pytest.mark.django_db

HOME_BUDGET = 20
PAGE_BUDGET = 28
LISTING_BUDGET = 29
ARTICLE_BUDGET = 31


@pytest.fixture
def images(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return [
        Image.objects.create(
            title=f"Foto {n}", file=get_test_image_file(size=(800, 600))
        )
        for n in range(6)
    ]


def _image(image):
    return {"image": image.pk, "alt_text": "x", "decorative": False}


def _body(images):
    stream_block = ContentStreamBlock()
    raw = [
        {"type": "hero", "value": {"title": "<p>T</p>", "image": _image(images[0])}},
        {
            "type": "cards",
            "value": {
                "cards": [
                    {"title": f"Tarjeta {n}", "image": _image(image)}
                    for n, image in enumerate(images)
                ]
            },
        },
        {
            "type": "gallery",
            "value": {"images": [{"image": _image(image)} for image in images]},
        },
    ]
    return stream_block.clean(stream_block.to_python(raw))


def _publish(parent, page):
    parent.add_child(instance=page)
    page.save_revision().publish()
    return page


def _queries(client, url):
    # The first visit generates renditions and fills the menu cache.
    client.get(url)
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)
    assert response.status_code == 200
    return len(queries)


@pytest.fixture
def listing(home_page, images):
    index = _publish(home_page, ArticleIndexPage(title="Novedades", slug="novedades"))
    for number in range(12):
        _publish(
            index,
            ArticlePage(
                title=f"Nota {number}",
                slug=f"nota-{number}",
                summary="Resumen",
                image=images[number % len(images)],
                image_alt="x",
                date=datetime.date(2026, 1, number + 1),
            ),
        )
    return index


def test_home(client, home_page):
    assert _queries(client, home_page.url) <= HOME_BUDGET


def test_page_with_blocks_does_not_grow_with_images(client, home_page, images):
    few = _publish(
        home_page, ContentPage(title="Dos", slug="dos", body=_body(images[:2]))
    )
    many = _publish(
        home_page, ContentPage(title="Seis", slug="seis", body=_body(images))
    )

    few_queries = _queries(client, few.url)

    assert few_queries <= PAGE_BUDGET
    assert _queries(client, many.url) == few_queries


def test_listing_does_not_grow_with_articles(client, listing):
    many_queries = _queries(client, listing.url)
    for article in ArticlePage.objects.order_by("date")[2:]:
        article.unpublish()

    assert many_queries <= LISTING_BUDGET
    assert _queries(client, listing.url) == many_queries


def test_article(client, listing):
    article = ArticlePage.objects.first()

    assert _queries(client, article.url) <= ARTICLE_BUDGET
