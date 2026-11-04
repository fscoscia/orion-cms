import json
import re

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.urls import reverse
from wagtail.blocks import StreamBlockValidationError, StructBlockValidationError
from wagtail.documents.models import Document
from wagtail.fields import StreamField
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page
from wagtail.rich_text import RichText
from wagtail_localize.segments.extract import extract_segments

from demo.models import DemoPage
from orion.core.blocks import (
    BaseContentBlock,
    BodyStreamField,
    CarouselBlock,
    ContentStreamBlock,
    HeroBlock,
    HighlightedTitleBlock,
    ImageContentBlock,
    RichTextBodyBlock,
    SiteStreamBlock,
    VideoBlock,
)
from orion.core.blocks.content import BlockStyleSelect
from orion.pages.models import ContentPage
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db

BLOCK_TYPES = [
    "hero",
    "text",
    "image",
    "gallery",
    "image_text",
    "cards",
    "stats",
    "tabs",
    "accordion",
    "call_to_action",
    "logos",
    "contact",
    "buttons",
    "latest_articles",
    "map",
    "form",
    "video",
    "carousel",
]

MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 16


@pytest.fixture
def image(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return Image.objects.create(
        title="Foto", file=get_test_image_file(size=(1600, 900))
    )


@pytest.fixture
def image_value(image):
    return {"image": image.pk, "alt_text": "Una foto", "decorative": False}


@pytest.fixture
def publish(home_page):
    """Publish a DemoPage with the given raw body and return it.

    The body is validated like the admin form does, which also stores it in the
    current StreamField format (with ids for list items).
    """

    def _publish(*blocks, slug="demo"):
        stream_block = ContentStreamBlock()
        raw = [{"type": block_type, "value": value} for block_type, value in blocks]
        body = stream_block.clean(stream_block.to_python(raw))
        page = home_page.add_child(
            instance=DemoPage(title="Demo", slug=slug, body=body)
        )
        page.save_revision().publish()
        return page

    return _publish


@pytest.fixture
def render(client, publish):
    """Publish a DemoPage with the given blocks and return its <main> HTML."""

    def _render(*blocks):
        page = publish(*blocks)
        html = client.get(page.url).content.decode()
        return html.split("<main", 1)[1].split("</main>", 1)[0]

    return _render


@pytest.fixture
def video(image):
    return Document.objects.create(title="Clip", file=ContentFile(MP4, name="clip.mp4"))


@pytest.fixture
def pdf(image):
    return Document.objects.create(
        title="Informe", file=ContentFile(b"%PDF-1.7", name="informe.pdf")
    )


def _tags(html, tag):
    return re.findall(rf"<{tag}\b[^>]*>", html)


def _slides(image_value, **first):
    return [{"image": image_value, **first}, {"image": image_value}]


class TestBody:
    def test_demo_page_renders_its_body(self, render):
        html = render(("text", {"body": "<p>Hola</p>"}))

        assert "<p>Hola</p>" in html

    def test_body_offers_every_block(self):
        assert list(ContentStreamBlock().child_blocks) == BLOCK_TYPES

    def test_hidden_block_is_not_shown_but_keeps_its_content(self, render):
        html = render(("text", {"body": "<p>Oculto</p>", "is_visible": False}))

        assert "Oculto" not in html
        stored = DemoPage.objects.get(slug="demo").body
        assert stored[0].value["body"].source == "<p>Oculto</p>"

    def test_blocks_are_visible_by_default(self):
        assert HeroBlock().child_blocks["is_visible"].get_default() is True

    def test_style_and_visible_are_in_the_editor_settings_area(self):
        # The editor only renders the fields listed in the form layout.
        layout = HeroBlock().meta.form_layout

        assert layout.children == ["eyebrow", "title", "intro", "buttons", "image"]
        assert layout.settings == ["anchor", "style", "is_visible"]


class TestHeroPosition:
    @staticmethod
    def _clean(*block_types):
        stream_block = ContentStreamBlock()
        values = {
            "hero": {"title": "<p>Hero</p>"},
            "text": {"body": "<p>Texto</p>"},
        }
        raw = [{"type": name, "value": values[name]} for name in block_types]
        return stream_block.clean(stream_block.to_python(raw))

    def test_hero_first_is_accepted(self):
        assert len(self._clean("hero", "text")) == 2

    def test_hero_after_another_block_is_rejected(self):
        with pytest.raises(StreamBlockValidationError) as error:
            self._clean("text", "hero")

        assert list(error.value.block_errors) == [1]

    def test_second_hero_is_rejected(self):
        with pytest.raises(StreamBlockValidationError):
            self._clean("hero", "hero")


class TestStyles:
    def test_project_style_reaches_the_template(self, render, settings):
        settings.ORION_BLOCK_STYLES = {"text": [("wide", "Ancho")]}

        html = render(("text", {"body": "<p>x</p>", "style": "wide"}))

        assert "block-text--wide" in html

    def test_removed_style_falls_back_to_default(self, render, settings):
        settings.ORION_BLOCK_STYLES = {"text": [("wide", "Ancho")]}
        page_html = render(("text", {"body": "<p>x</p>", "style": "wide"}))
        assert "block-text--wide" in page_html
        settings.ORION_BLOCK_STYLES = {}

        stored = DemoPage.objects.get(slug="demo").body

        assert stored[0].value["style"] == "default"

    def test_single_style_renders_a_hidden_input(self):
        widget = BlockStyleSelect(choices=[("default", "Estándar")])

        html = widget.render("style", "default")

        assert 'type="hidden"' in html
        assert "<select" not in html

    def test_several_styles_render_a_select(self):
        widget = BlockStyleSelect(choices=[("default", "Estándar"), ("wide", "Ancho")])

        assert "<select" in widget.render("style", "default")

    def test_changing_styles_needs_no_migration(self, settings):
        settings.ORION_BLOCK_STYLES = {"hero": [("split", "Imagen al costado")]}

        call_command("makemigrations", "--check", "--dry-run", verbosity=0)


class TestTitles:
    def test_bold_words_are_highlighted_in_a_single_heading(self, render):
        html = render(("hero", {"title": "<p>Cuidamos <b>tu salud</b></p>"}))

        assert re.search(
            r'<h1 class="orion-title[^"]*">Cuidamos <b>tu salud</b></h1>', html
        )

    def test_title_only_allows_bold(self):
        assert HighlightedTitleBlock().features == ["bold"]

    def test_title_with_two_paragraphs_is_rejected(self):
        block = HighlightedTitleBlock()

        with pytest.raises(ValidationError):
            block.clean(RichText("<p>Uno</p><p>Dos</p>"))

    def test_body_text_allows_editorial_formats_only(self):
        assert RichTextBodyBlock().features == [
            "h2",
            "h3",
            "bold",
            "italic",
            "link",
            "ol",
            "ul",
        ]


class TestButtons:
    def test_button_to_unpublished_page_is_hidden(self, render, services_page):
        services_page.unpublish()

        html = render(
            (
                "hero",
                {
                    "title": "<p>T</p>",
                    "buttons": [{"label": "Ir", "page": services_page.pk}],
                },
            )
        )

        assert "orion-button" not in html

    def test_empty_button_list_renders_no_markup(self, render):
        html = render(("hero", {"title": "<p>T</p>", "buttons": []}))

        assert "orion-buttons" not in html

    def test_new_tab_button_is_safe(self, render):
        html = render(
            (
                "call_to_action",
                {
                    "title": "<p>T</p>",
                    "buttons": [
                        {
                            "label": "Ir",
                            "url": "https://example.org/",
                            "open_in_new_tab": True,
                        }
                    ],
                },
            )
        )

        assert 'target="_blank" rel="noopener noreferrer"' in html

    def test_buttons_block_alignment(self, render):
        html = render(
            (
                "buttons",
                {"alignment": "center", "buttons": [{"label": "B", "email": "a@b.co"}]},
            )
        )

        assert "justify-center" in html
        assert 'href="mailto:a@b.co"' in html


class TestImages:
    def test_image_without_alt_text_is_rejected(self, image):
        block = ImageContentBlock()
        value = block.to_python(
            {"image": {"image": image.pk, "alt_text": "", "decorative": False}}
        )

        with pytest.raises(StructBlockValidationError):
            block.clean(value)

    def test_decorative_image_has_empty_alt(self, render, image):
        html = render(
            (
                "image",
                {"image": {"image": image.pk, "alt_text": "", "decorative": True}},
            )
        )

        assert 'alt=""' in _tags(html, "img")[0]

    def test_gallery_images_are_responsive_and_lazy(self, render, image_value):
        html = render(("gallery", {"images": [{"image": image_value}] * 2}))

        assert html.count("<picture>") == 2
        sources = _tags(html, "source")
        assert len(sources) == 2
        assert all('type="image/avif"' in tag and "sizes=" in tag for tag in sources)
        for tag in _tags(html, "img"):
            assert ".webp " in tag.split('srcset="', 1)[1]
            assert 'width="' in tag
            assert 'height="' in tag
            assert 'loading="lazy"' in tag

    def test_hero_image_loads_immediately(self, render, image_value):
        html = render(("hero", {"title": "<p>T</p>", "image": image_value}))

        assert 'loading="lazy"' not in _tags(html, "img")[0]
        assert 'fetchpriority="high"' in _tags(html, "img")[0]

    def test_page_starting_with_a_hero_preloads_its_image(
        self, client, publish, image_value
    ):
        page = publish(("hero", {"title": "<p>T</p>", "image": image_value}))

        html = client.get(page.url).content.decode()

        head = html.split("</head>", 1)[0]
        preload = next(tag for tag in _tags(head, "link") if 'rel="preload"' in tag)
        avif_source = next(tag for tag in _tags(html, "source") if "image/avif" in tag)
        srcset = avif_source.split('srcset="', 1)[1].split('"', 1)[0]
        assert 'type="image/avif"' in preload
        assert f'imagesrcset="{srcset}"' in preload
        assert 'fetchpriority="high"' in preload

    def test_page_without_a_leading_hero_does_not_preload(
        self, client, publish, image_value
    ):
        page = publish(("image", {"image": image_value}))

        head = client.get(page.url).content.decode().split("</head>", 1)[0]

        assert 'rel="preload"' not in head

    def test_headings_keep_a_valid_outline(self, render):
        html = render(
            ("hero", {"title": "<p>Inicio</p>"}),
            ("cards", {"title": "<p>Servicios</p>", "cards": [{"title": "Uno"}]}),
        )

        headings = re.findall(r"<(h[1-6])\b", html)

        assert headings == ["h1", "h2", "h3"]


class TestCardsAndLogos:
    def test_columns_choose_the_grid(self, render):
        html = render(("cards", {"columns": "4", "cards": [{"title": "Uno"}]}))

        assert "lg:grid-cols-4" in html

    def test_card_link_uses_the_page_title(self, render, services_page):
        html = render(
            ("cards", {"cards": [{"title": "Uno", "link": {"page": services_page.pk}}]})
        )

        assert re.search(r'<a href="/servicios/"[^>]*>Servicios</a>', html)

    def test_linked_logo_is_named_by_its_alt_text(self, render, image):
        html = render(
            (
                "logos",
                {
                    "logos": [
                        {"image": image.pk, "name": "Acme", "url": "https://a.test/"}
                    ]
                },
            )
        )

        link = re.search(r'<a href="https://a.test/".*?</a>', html, re.S).group()
        assert 'alt="Acme"' in link


class TestContact:
    @pytest.fixture
    def site_settings(self):
        site_settings = SiteSettings.load()
        site_settings.phone = "+595 21 729 1444"
        site_settings.email = ""
        site_settings.save()
        return site_settings

    def test_shows_chosen_site_data_and_extra_items(self, render, site_settings):
        html = render(
            (
                "contact",
                {
                    "show_whatsapp": False,
                    "extra_items": [{"label": "Horario", "text": "Lunes a viernes"}],
                },
            )
        )

        assert 'href="tel:+595217291444"' in html
        assert "mailto:" not in html
        assert "Horario" in html
        assert "Lunes a viernes" in html

    def test_reflects_changes_in_site_data(self, render, client, site_settings):
        render(("contact", {}))
        site_settings.phone = "+595 21 000 000"
        site_settings.save()

        html = client.get("/demo/").content.decode()

        assert "+595 21 000 000" in html


class TestInteractiveBlocks:
    def test_tabs_markup_and_unique_ids(self, render):
        tabs = {
            "tabs": [
                {"title": "A", "body": "<p>a</p>"},
                {"title": "B", "body": "<p>b</p>"},
            ]
        }

        html = render(("tabs", tabs), ("tabs", tabs))

        tab_ids = re.findall(r'role="tab" id="([^"]+)"', html)
        assert len(tab_ids) == 4
        assert len(set(tab_ids)) == 4
        assert 'role="tablist" hidden' in html
        for tab_id in tab_ids:
            panel_id = tab_id.replace("tab-", "tab-panel-", 1)
            assert f'aria-controls="{panel_id}"' in html
            assert f'id="{panel_id}"' in html

    def test_accordion_uses_native_disclosure(self, render):
        html = render(
            ("accordion", {"items": [{"title": "¿Dónde?", "body": "<p>Acá</p>"}]})
        )

        assert "<details" in html
        assert "<summary" in html

    def test_stats_render_the_final_number(self, render):
        html = render(
            ("stats", {"stats": [{"number": 186, "prefix": "+", "label": "x"}]})
        )

        assert 'x-text="display">186<' in html
        assert '<span class="sr-only">+186 </span>' in html


class TestVideo:
    def _value(self, video, image_value, **fields):
        return {"video": video.pk, "cover": image_value, **fields}

    def test_controls_video_waits_for_the_visitor(self, render, video, image_value):
        html = render(("video", self._value(video, image_value)))

        tag = _tags(html, "video")[0]
        assert 'preload="none"' in tag and "controls" in tag
        assert "autoplay" not in tag and "muted" not in tag
        assert f'src="{video.file.url}"' in html and 'type="video/mp4"' in html
        assert "data-ambient" not in html
        assert "aspect-video" in html
        assert re.search(r'class="orion-video__play"[^>]*\bhidden\b', html)

    def test_cover_is_lazy_and_sized(self, render, video, image_value):
        html = render(("video", self._value(video, image_value)))

        tag = _tags(html, "img")[0]
        assert 'loading="lazy"' in tag
        assert 'width="' in tag and 'height="' in tag

    def test_ambient_vertical_video(self, render, video, image_value):
        html = render(
            (
                "video",
                self._value(video, image_value, mode="ambient", orientation="portrait"),
            )
        )

        tag = _tags(html, "video")[0]
        assert "muted" in tag and "loop" in tag and "playsinline" in tag
        assert "controls" not in tag and "autoplay" not in tag
        assert "data-ambient" in html and "aspect-9/16" in html
        assert 'aria-pressed="false" hidden' in html

    def test_video_url_keeps_the_media_url(self, render, video, image_value, settings):
        settings.MEDIA_URL = "/sub/media/"

        html = render(("video", self._value(video, image_value)))

        assert 'src="/sub/media/' in html

    def test_document_that_is_not_a_video_is_rejected(self, pdf, image_value):
        block = VideoBlock()

        with pytest.raises(StructBlockValidationError) as error:
            block.clean(block.to_python(self._value(pdf, image_value)))

        assert "MP4" in str(error.value.block_errors["video"])

    def test_cover_is_required(self, video):
        block = VideoBlock()

        with pytest.raises(StructBlockValidationError) as error:
            block.clean(block.to_python({"video": video.pk}))

        assert "cover" in error.value.block_errors


class TestCarousel:
    def test_slides_keep_their_order_and_content(self, render, image_value):
        html = render(
            (
                "carousel",
                {
                    "slides": [
                        {"image": image_value, "title": "Uno", "text": "Texto uno"},
                        {"image": image_value, "title": "Dos"},
                    ]
                },
            )
        )

        assert html.index("Uno") < html.index("Texto uno") < html.index("Dos")
        assert html.count("orion-carousel__slide") == 2
        assert html.count("orion-carousel__dot") == 2

    def test_controls_start_hidden(self, render, image_value):
        html = render(("carousel", {"slides": _slides(image_value)}))

        assert re.search(r'class="orion-carousel__controls"[^>]*\bhidden\b', html)
        assert 'x-data="carousel"' in html

    def test_layouts(self, render, image_value):
        html = render(("carousel", {"layout": "cards", "slides": _slides(image_value)}))

        assert "orion-carousel--cards" in html
        assert "aspect-3/4" in html

    def test_slide_titles_sit_under_the_block_title(self, render, image_value):
        slides = _slides(image_value, title="Diapositiva")

        with_title = render(("carousel", {"title": "<p>Título</p>", "slides": slides}))
        assert re.search(r"<h3[^>]*>Diapositiva</h3>", with_title)

    def test_slide_titles_are_h2_without_a_block_title(self, render, image_value):
        html = render(
            ("carousel", {"slides": _slides(image_value, title="Diapositiva")})
        )

        assert re.search(r"<h2[^>]*>Diapositiva</h2>", html)

    def test_slide_video_is_ambient(self, render, image_value, video):
        html = render(("carousel", {"slides": _slides(image_value, video=video.pk)}))

        tag = _tags(html, "video")[0]
        assert "muted" in tag and "controls" not in tag and "autoplay" not in tag

    def test_needs_two_slides(self, image_value):
        block = CarouselBlock()

        with pytest.raises(StructBlockValidationError):
            block.clean(block.to_python({"slides": [{"image": image_value}]}))

    def test_allows_twelve_slides_at_most(self, image_value):
        block = CarouselBlock()

        with pytest.raises(StructBlockValidationError):
            block.clean(block.to_python({"slides": [{"image": image_value}] * 13}))

    def test_document_that_is_not_a_video_is_rejected(self, pdf, image_value):
        block = CarouselBlock()
        value = block.to_python({"slides": _slides(image_value, video=pdf.pk)})

        with pytest.raises(StructBlockValidationError):
            block.clean(value)


class TestLeadingCarousel:
    def _page(self, home_page, *blocks):
        stream_block = ContentStreamBlock()
        raw = [{"type": block_type, "value": value} for block_type, value in blocks]
        page = home_page.add_child(
            instance=ContentPage(
                title="Con carrusel",
                slug="con-carrusel",
                body=stream_block.clean(stream_block.to_python(raw)),
            )
        )
        page.save_revision().publish()
        return page

    def _html(self, client, page):
        return client.get(page.url).content.decode()

    def _main(self, client, page):
        return self._html(client, page).split("<main", 1)[1].split("</main>", 1)[0]

    def test_full_carousel_keeps_the_page_title_for_screen_readers(
        self, client, home_page, image_value
    ):
        page = self._page(
            home_page,
            ("carousel", {"slides": _slides(image_value, title="Mensaje")}),
        )

        h1_tags = re.findall(r"<h1\b[^>]*>[^<]*</h1>", self._main(client, page))
        assert len(h1_tags) == 1
        assert 'class="sr-only"' in h1_tags[0] and "Con carrusel" in h1_tags[0]

    def test_cards_carousel_shows_the_page_title(self, client, home_page, image_value):
        page = self._page(
            home_page,
            ("carousel", {"layout": "cards", "slides": _slides(image_value)}),
        )

        h1_tags = re.findall(r"<h1\b[^>]*>", self._main(client, page))
        assert len(h1_tags) == 1 and "sr-only" not in h1_tags[0]

    def test_hidden_carousel_does_not_take_the_title(
        self, client, home_page, image_value
    ):
        page = self._page(
            home_page,
            (
                "carousel",
                {"is_visible": False, "slides": _slides(image_value)},
            ),
        )

        assert "sr-only" not in re.findall(r"<h1\b[^>]*>", self._main(client, page))[0]

    def test_first_image_is_fetched_first_and_preloaded(
        self, client, home_page, image_value
    ):
        page = self._page(home_page, ("carousel", {"slides": _slides(image_value)}))

        html = self._html(client, page)
        head, main = html.split("<main", 1)
        images = _tags(main, "img")
        assert 'fetchpriority="high"' in images[0]
        assert "loading=" not in images[0]
        assert 'loading="lazy"' in images[1]
        assert 'rel="preload" as="image" type="image/avif"' in head

    def test_carousel_further_down_stays_lazy(self, client, home_page, image_value):
        page = self._page(
            home_page,
            ("text", {"body": "<p>Hola</p>"}),
            ("carousel", {"slides": _slides(image_value)}),
        )

        html = self._html(client, page)
        assert 'rel="preload" as="image"' not in html
        images = _tags(html.split("<main", 1)[1], "img")
        assert all('loading="lazy"' in tag for tag in images)

    def test_cards_carousel_stays_lazy(self, client, home_page, image_value):
        page = self._page(
            home_page,
            ("carousel", {"layout": "cards", "slides": _slides(image_value)}),
        )

        images = _tags(self._main(client, page), "img")
        assert all('loading="lazy"' in tag for tag in images)


class TestBlockMigration:
    def test_migration_only_changes_block_definitions(self):
        from importlib import import_module

        from django.db import migrations

        migration = import_module(
            "orion.pages.migrations.0007_video_carousel_blocks"
        ).Migration

        assert all(isinstance(op, migrations.AlterField) for op in migration.operations)
        assert {op.name for op in migration.operations} == {"body"}


class TestEditor:
    @pytest.mark.parametrize("block_type", BLOCK_TYPES)
    def test_each_block_has_a_description_and_a_preview(self, admin_client, block_type):
        block = ContentStreamBlock().child_blocks[block_type]

        response = admin_client.get(
            reverse("wagtailadmin_block_preview"), {"id": block.definition_prefix}
        )

        assert block.get_description()
        assert block.is_previewable
        assert response.status_code == 200
        assert "orion/css/orion.css" in response.content.decode()

    @pytest.mark.parametrize(
        "block_type",
        ["hero", "image", "gallery", "image_text", "cards", "logos", "latest_articles"],
    )
    def test_previews_use_sample_content_without_touching_the_site(
        self, admin_client, block_type
    ):
        block = ContentStreamBlock().child_blocks[block_type]
        pages_before = Page.objects.count()

        html = admin_client.get(
            reverse("wagtailadmin_block_preview"), {"id": block.definition_prefix}
        ).content.decode()

        assert re.search(r'<img src="/static/orion/samples/[\w-]+\.(webp|svg)"', html)
        assert Image.objects.count() == 0
        assert Page.objects.count() == pages_before


class TestTranslation:
    def test_text_of_blocks_is_extracted_for_translation(
        self, publish, image_value, services_page
    ):
        page = publish(
            (
                "hero",
                {
                    "title": "<p>Título del hero</p>",
                    "intro": "Texto de apoyo",
                    "image": image_value,
                    "buttons": [{"label": "Botón", "page": services_page.pk}],
                },
            ),
            ("tabs", {"tabs": [{"title": "Pestaña", "body": "<p>Panel</p>"}] * 2}),
        )

        texts = {
            str(segment.string.data)
            for segment in extract_segments(page)
            if hasattr(segment, "string")
        }

        for text in (
            "Título del hero",
            "Texto de apoyo",
            "Botón",
            "Una foto",
            "Pestaña",
            "Panel",
        ):
            assert text in texts

    def test_button_follows_the_visitor_language(
        self,
        client,
        publish,
        home_page,
        services_page,
        english_locale,
        make_language_public,
        translate_page,
    ):
        page = publish(
            ("buttons", {"buttons": [{"label": "Ir", "page": services_page.pk}]})
        )
        make_language_public(english_locale)
        translate_page(home_page, english_locale)
        translate_page(services_page, english_locale, slug="services")
        translate_page(page, english_locale)

        html = client.get("/en/demo/").content.decode()

        assert 'href="/en/services/"' in html


class TestNewBlockTranslation:
    def test_video_and_carousel_texts_are_offered(self, publish, video, image_value):
        page = publish(
            (
                "video",
                {"video": video.pk, "cover": image_value, "caption": "Pie del video"},
            ),
            (
                "carousel",
                {"slides": _slides(image_value, title="Título", text="Mensaje")},
            ),
        )

        texts = {
            segment.string.data
            for segment in extract_segments(page)
            if hasattr(segment, "string")
        }

        assert {"Pie del video", "Título", "Mensaje"} <= texts


TITLED_BLOCKS = {
    "hero",
    "gallery",
    "image_text",
    "cards",
    "stats",
    "tabs",
    "accordion",
    "call_to_action",
    "logos",
    "contact",
    "latest_articles",
    "map",
    "form",
    "video",
    "carousel",
}


class TestEyebrow:
    def test_only_blocks_with_a_title_offer_it(self):
        blocks = ContentStreamBlock().child_blocks

        offering = {
            name for name, block in blocks.items() if "eyebrow" in block.child_blocks
        }

        assert offering == TITLED_BLOCKS

    def test_is_shown_above_the_title_as_a_paragraph(self, render):
        html = render(
            (
                "accordion",
                {
                    "eyebrow": "Dudas",
                    "title": "<p>Preguntas</p>",
                    "items": [{"title": "Uno", "body": "<p>Dos</p>"}],
                },
            )
        )

        assert re.search(r'<p class="orion-eyebrow">Dudas</p>\s*<h2', html)

    def test_block_without_eyebrow_keeps_its_markup(self, render):
        html = render(
            (
                "accordion",
                {
                    "title": "<p>Preguntas</p>",
                    "items": [{"title": "Uno", "body": "<p>Dos</p>"}],
                },
            )
        )

        assert "orion-eyebrow" not in html and "orion-heading" not in html

    def test_without_a_title_there_is_no_empty_heading(self, render):
        html = render(
            (
                "accordion",
                {
                    "eyebrow": "Dudas",
                    "items": [{"title": "Uno", "body": "<p>Dos</p>"}],
                },
            )
        )

        assert "Dudas" in html and "<h2" not in html

    def test_hero_keeps_a_single_h1(self, render):
        html = render(("hero", {"eyebrow": "Novedad", "title": "<p>Hola</p>"}))

        assert re.search(r'<p class="orion-eyebrow">Novedad</p>\s*<h1', html)
        assert html.count("<h1") == 1


class TestAnchors:
    TEXT = {"body": "<p>Hola</p>"}

    def _clean(self, *values):
        stream_block = ContentStreamBlock()
        raw = [{"type": "text", "value": value} for value in values]
        return stream_block.clean(stream_block.to_python(raw))

    def test_anchor_is_the_id_of_the_block(self, render):
        html = render(("text", {**self.TEXT, "anchor": "categorias"}))

        assert '<div class="block-text" id="categorias">' in html

    def test_block_without_anchor_has_no_id(self, render):
        assert '<div class="block-text">' in render(("text", self.TEXT))

    def test_hidden_block_leaves_no_id(self, render):
        html = render(("text", {**self.TEXT, "anchor": "oculta", "is_visible": False}))

        assert "oculta" not in html

    @pytest.mark.parametrize(
        "anchor", ["#categorias", "Categorias", "con espacio", "-inicio", "fin-", "ñu"]
    )
    def test_invalid_format_is_rejected(self, anchor):
        with pytest.raises(StreamBlockValidationError):
            self._clean({**self.TEXT, "anchor": anchor})

    def test_repeated_anchor_marks_the_second_block(self):
        with pytest.raises(StreamBlockValidationError) as error:
            self._clean(
                {**self.TEXT, "anchor": "requisitos"},
                {**self.TEXT, "anchor": "requisitos"},
            )

        assert set(error.value.block_errors) == {1}

    def test_hidden_blocks_count_as_repeated(self):
        with pytest.raises(StreamBlockValidationError):
            self._clean(
                {**self.TEXT, "anchor": "requisitos", "is_visible": False},
                {**self.TEXT, "anchor": "requisitos"},
            )

    @pytest.mark.parametrize("anchor", ["main-content", "site-nav-panel"])
    def test_reserved_anchor_is_rejected(self, anchor):
        with pytest.raises(StreamBlockValidationError) as error:
            self._clean({**self.TEXT, "anchor": anchor})

        assert set(error.value.block_errors) == {0}

    def test_project_blocks_inherit_it(self):
        class ProjectBlock(BaseContentBlock):
            style_key = "project"

        assert "anchor" in ProjectBlock().child_blocks

    def test_content_saved_before_the_fields_still_renders(self, home_page, client):
        page = home_page.add_child(
            instance=ContentPage(
                title="Vieja",
                slug="vieja",
                body=json.dumps(
                    [
                        {
                            "type": "text",
                            "id": "11111111-1111-1111-1111-111111111111",
                            "value": {
                                "body": "<p>Contenido viejo</p>",
                                "style": "default",
                                "is_visible": True,
                            },
                        }
                    ]
                ),
            )
        )

        html = client.get(page.url).content.decode()

        assert "Contenido viejo" in html
        assert '<div class="block-text">' in html

    def test_eyebrow_is_offered_and_anchor_is_not(self, publish, image_value):
        page = publish(
            (
                "cards",
                {
                    "eyebrow": "Beneficios",
                    "anchor": "beneficios",
                    "cards": [{"title": "Uno"}],
                },
            )
        )

        texts = {
            segment.string.data
            for segment in extract_segments(page)
            if hasattr(segment, "string")
        }

        assert "Beneficios" in texts and "beneficios" not in texts


class TestDefinitionMigrations:
    @pytest.mark.parametrize(
        ("module", "field"),
        [
            ("orion.pages.migrations.0008_block_eyebrow_and_anchors", "body"),
            ("orion.navigation.migrations.0003_link_anchors", "items"),
        ],
    )
    def test_they_only_change_block_definitions(self, module, field):
        from importlib import import_module

        from django.db import migrations

        operations = import_module(module).Migration.operations

        assert all(isinstance(op, migrations.AlterField) for op in operations)
        assert {op.name for op in operations} == {field}


class TestProjectBlocks:
    PROJECT_BLOCKS = {"project_text": "orion.core.blocks.TextContentBlock"}

    def test_the_project_block_joins_orions(self, settings):
        settings.ORION_PROJECT_BLOCKS = self.PROJECT_BLOCKS

        child_blocks = SiteStreamBlock().child_blocks

        assert "project_text" in child_blocks
        assert child_blocks["project_text"].name == "project_text"
        assert "hero" in child_blocks

    def test_without_project_blocks_only_orions_are_offered(self):
        assert list(SiteStreamBlock().child_blocks) == list(
            ContentStreamBlock().child_blocks
        )

    def test_migrations_do_not_see_project_blocks(self, settings):
        settings.ORION_PROJECT_BLOCKS = self.PROJECT_BLOCKS
        field = BodyStreamField(SiteStreamBlock(), blank=True)

        _name, path, args, kwargs = field.deconstruct()
        _name, _path, plain_args, plain_kwargs = StreamField(
            ContentStreamBlock(), blank=True
        ).deconstruct()

        assert path == "wagtail.fields.StreamField"
        assert args == plain_args
        assert kwargs == plain_kwargs
