import pytest
from django.urls import reverse

from orion.pages.models import ArticleIndexPage, ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture
def content_page(home_page):
    page = ContentPage(title="Nosotros", slug="nosotros")
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


class TestPreviewSize:
    @pytest.mark.parametrize("page_class", [ContentPage, ArticleIndexPage])
    def test_orion_pages_preview_at_desktop_size(self, page_class):
        page = page_class(title="X")

        assert page.default_preview_size == "desktop"
        assert [size["name"] for size in page.preview_sizes] == [
            "mobile",
            "tablet",
            "desktop",
        ]


class TestEditorScript:
    def test_editor_loads_the_script_with_its_labels(self, admin_client, content_page):
        html = admin_client.get(
            reverse("wagtailadmin_pages:edit", args=[content_page.pk])
        ).content.decode()

        assert 'src="/static/orion/editor/editor.js"' in html
        assert 'data-preview-label="' in html
        assert 'data-edit-label="' in html


class TestLinksInPreview:
    def test_preview_blocks_links(self, content_page):
        response = content_page.make_preview_request()

        assert "orion/js/preview.js" in response.content.decode()

    def test_published_page_does_not(self, client, content_page):
        html = client.get(content_page.url).content.decode()

        assert "orion/js/preview.js" not in html
