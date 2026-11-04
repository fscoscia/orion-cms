import io
import re
from types import SimpleNamespace

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.signals import request_started
from django.urls import reverse
from PIL import Image as PillowImage
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file, get_test_image_file_svg
from wagtail.models import Collection

from orion.core import image_library
from orion.core.image_library import generate_renditions
from orion.core.images import all_filter_specs
from orion.pages.models import ArticleIndexPage, ArticlePage, ContentPage
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db

SVG_WITH_SCRIPT = b"""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="200" height="48" viewBox="0 0 200 48" onload="alert(1)">
  <script>alert(2)</script>
  <style>.a { fill: #1e3a8a; }</style>
  <foreignObject width="10" height="10"><p>html</p></foreignObject>
  <rect class="a" width="200" height="48" onclick="alert(3)"/>
  <a href="javascript:alert(4)"><circle cx="24" cy="24" r="12"/></a>
  <use xlink:href="https://evil.example/x.svg#a"/>
  <use href="#local"/>
  <path id="local" d="M0 0h10v10z" style="fill: url(https://evil.example/p)"/>
</svg>"""


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def _image(size=(1600, 900), title="Foto"):
    return Image.objects.create(title=title, file=get_test_image_file(size=size))


def _svg(content=SVG_WITH_SCRIPT, name="logo.svg"):
    return Image.objects.create(title="Logo", file=ContentFile(content, name=name))


def _png(size):
    file = get_test_image_file(size=size)
    return SimpleUploadedFile("foto.png", file.file.getvalue(), "image/png")


def _upload(client, file, title="Nueva"):
    return client.post(
        reverse("wagtailimages:add"),
        {
            "title": title,
            "file": file,
            "collection": Collection.get_first_root_node().pk,
        },
    )


class TestReduction:
    def test_large_original_is_reduced(self):
        image = _image(size=(6000, 4000))

        image.refresh_from_db()
        with image.open_file() as file, PillowImage.open(file) as stored:
            stored_size = stored.size
        assert (image.width, image.height) == (2048, 1365)
        assert stored_size == (2048, 1365)
        assert image.file_size == image.file.size

    def test_small_original_is_kept(self):
        image = _image(size=(1600, 900))

        assert (image.width, image.height) == (1600, 900)

    def test_upload_from_the_admin_is_reduced(self, admin_client):
        _upload(admin_client, _png((4096, 1024)))

        image = Image.objects.get(title="Nueva")
        assert (image.width, image.height) == (2048, 512)


class TestUploadLimits:
    def test_format_not_allowed(self, admin_client):
        response = _upload(
            admin_client, SimpleUploadedFile("foto.bmp", b"BM not really")
        )

        assert response.status_code == 200
        assert not Image.objects.exists()

    def test_too_heavy(self, settings, admin_client):
        settings.WAGTAILIMAGES_MAX_UPLOAD_SIZE = 1024

        response = _upload(admin_client, _png((1200, 1200)))

        assert response.status_code == 200
        assert not Image.objects.exists()


class TestRenditions:
    def test_generated_when_uploaded(self, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            image = _image()

        filter_specs = set(image.renditions.values_list("filter_spec", flat=True))
        assert filter_specs == set(all_filter_specs(image))
        assert any(spec.endswith("format-avif") for spec in filter_specs)

    def test_new_focal_point_generates_new_crops(
        self, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            image = _image()
        count = image.renditions.count()

        image.focal_point_x, image.focal_point_y = 100, 100
        image.focal_point_width = image.focal_point_height = 50
        with django_capture_on_commit_callbacks(execute=True):
            image.save()

        assert image.renditions.count() > count

    def test_command_creates_the_missing_ones(self):
        image = _image()
        image.renditions.all().delete()
        out = io.StringIO()

        call_command("orion_generate_renditions", stdout=out)
        again = io.StringIO()
        call_command("orion_generate_renditions", stdout=again)

        # Several sizes share filters (e.g. "image" and "article").
        created = len(set(all_filter_specs(image)))
        assert f"Renditions created: {created}." in out.getvalue()
        assert "Renditions created: 0." in again.getvalue()

    def test_generation_skips_existing(self):
        image = _image()
        generate_renditions(image)

        assert generate_renditions(image) == 0


class TestSvg:
    def test_dangerous_content_is_removed(self):
        image = _svg()

        with image.open_file() as file:
            content = file.read().decode()
        for dangerous in (
            "script",
            "onload",
            "onclick",
            "foreignObject",
            "javascript:",
            "evil.example",
        ):
            assert dangerous not in content, dangerous
        assert "<rect" in content
        assert 'href="#local"' in content
        assert ".a { fill: #1e3a8a; }" in content
        assert (image.width, image.height) == (200, 48)

    def test_design_tool_doctype_is_accepted(self):
        image = Image.objects.create(title="Logo", file=get_test_image_file_svg())

        assert image.is_svg()

    def test_invalid_svg_is_rejected_in_the_admin(self, admin_client):
        response = _upload(
            admin_client, SimpleUploadedFile("roto.svg", b"<svg><unclosed></svg>")
        )

        assert response.status_code == 200
        assert response.context["form"].errors["file"]
        assert not Image.objects.exists()

    def test_entities_are_rejected(self, admin_client):
        bomb = (
            b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY a "aaaa">]>'
            b'<svg xmlns="http://www.w3.org/2000/svg">&a;</svg>'
        )

        response = _upload(admin_client, SimpleUploadedFile("bomba.svg", bomb))

        assert response.context["form"].errors["file"]

        assert not Image.objects.exists()

    def test_svg_is_shown_as_svg(self, django_capture_on_commit_callbacks):
        from django.template import Context, Template

        with django_capture_on_commit_callbacks(execute=True):
            image = _svg()

        html = Template(
            '{% load orion_core %}{% responsive_image image "logo" alt="Logo" %}'
        ).render(Context({"image": image}))

        assert "<picture" not in html
        assert re.search(r'<img [^>]*src="[^"]+\.svg"', html)


class TestUnusedImages:
    def _unused(self):
        out = io.StringIO()
        call_command("orion_unused_images", stdout=out)
        return out.getvalue()

    def test_lists_only_unused_images(self, home_page):
        orphan = _image(title="Huérfana")
        in_block = _image(title="En un bloque")
        in_article = _image(title="En un artículo")
        logo = _image(title="Logo del sitio")
        page = ContentPage(
            title="Nosotros",
            slug="nosotros",
            body=[("image", {"image": {"image": in_block, "alt_text": "x"}})],
        )
        home_page.add_child(instance=page)
        page.save_revision().publish()
        index = ArticleIndexPage(title="Novedades", slug="novedades")
        home_page.add_child(instance=index)
        article = ArticlePage(
            title="Uno", slug="uno", summary="x", image=in_article, image_alt="x"
        )
        index.add_child(instance=article)
        site_settings = SiteSettings.load()
        site_settings.logo = logo
        site_settings.save()

        output = self._unused()

        assert orphan.title in output
        for used in (in_block, in_article, logo):
            assert used.title not in output, used.title
        assert "Unused images: 1" in output
        assert Image.objects.count() == 4


class TestWhereVariantsAreGenerated:
    @pytest.fixture
    def threads(self, settings, monkeypatch):
        settings.ORION_IMAGE_RENDITIONS_IN_BACKGROUND = True
        started = []

        class FakeThread:
            def __init__(self, target, args, daemon):
                self.args = args

            def start(self):
                started.append(self.args)

        # Only Orion's module: Wagtail's thread pool needs the real class.
        monkeypatch.setattr(
            image_library, "threading", SimpleNamespace(Thread=FakeThread)
        )
        return started

    def test_outside_a_request_they_are_ready_when_saving_ends(
        self, threads, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            image = _image()

        assert threads == []
        assert image.renditions.exists()

    def test_inside_a_request_they_go_to_the_background(
        self, threads, django_capture_on_commit_callbacks
    ):
        # Directly: the real signals also close the test's database connection.
        image_library._mark_request_started()
        try:
            with django_capture_on_commit_callbacks(execute=True):
                image = _image()
        finally:
            image_library._mark_request_finished()

        assert threads == [(image.pk,)]
        assert not image.renditions.exists()

    def test_the_signals_mark_requests(self, threads, client, home_page):
        seen = []

        def spy(**kwargs):
            seen.append(image_library._current.is_in_request)

        request_started.connect(spy, weak=False)
        try:
            client.get("/")
        finally:
            request_started.disconnect(spy)

        assert seen == [True]
        assert image_library._current.is_in_request is False
