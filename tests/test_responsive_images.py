import re

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from orion.core.blocks.content import SampleImage

pytestmark = pytest.mark.django_db


@pytest.fixture
def image(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return Image.objects.create(
        title="Foto", file=get_test_image_file(size=(1600, 900))
    )


def _render(source, **context):
    return Template("{% load orion_core %}" + source).render(Context(context))


def _tags(html, tag):
    return re.findall(rf"<{tag}\b[^>]*>", html)


class TestResponsiveImage:
    def test_card_size(self, image):
        html = _render(
            '{% responsive_image image "card" alt="Una foto" class_name="w-full" %}',
            image=image,
        )

        sources = _tags(html, "source")
        img = _tags(html, "img")[0]
        assert html.startswith("<picture>")
        # AVIF as a source, WebP in the fallback <img>.
        assert len(sources) == 1
        assert 'type="image/avif"' in sources[0]
        for tag in (sources[0], img):
            assert " 480w" in tag and " 800w" in tag
        assert ".webp 480w" in img
        assert 'alt="Una foto"' in img
        assert 'class="w-full"' in img
        assert 'width="' in img and 'height="' in img
        assert 'loading="lazy"' in img and 'decoding="async"' in img

    def test_main_image(self, image):
        img = _tags(
            _render('{% responsive_image image "hero" is_main=True %}', image=image),
            "img",
        )[0]

        assert 'fetchpriority="high"' in img
        assert "loading=" not in img

    def test_not_lazy(self, image):
        img = _tags(
            _render(
                '{% responsive_image image "site_logo" is_lazy=False %}', image=image
            ),
            "img",
        )[0]

        assert "loading=" not in img
        assert "fetchpriority=" not in img

    def test_project_size(self, settings, image):
        settings.ORION_IMAGE_SIZES = {
            "team": {"filters": "fill-{300x300,600x600}", "sizes": "300px"}
        }

        html = _render('{% responsive_image image "team" %}', image=image)

        assert 'sizes="300px"' in html
        assert " 600w" in html

    def test_unknown_size(self, image):
        with pytest.raises(ImproperlyConfigured, match="'nope'"):
            _render('{% responsive_image image "nope" %}', image=image)

    def test_empty_image(self):
        assert _render('{% responsive_image image "card" %}', image=None) == ""

    def test_sample_image(self):
        html = _render(
            '{% responsive_image image "card" alt="Muestra" %}',
            image=SampleImage("landscape-1.webp", alt="Muestra"),
        )

        assert html.strip().startswith(
            '<img src="/static/orion/samples/landscape-1.webp"'
        )
