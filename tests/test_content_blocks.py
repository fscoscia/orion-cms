import re

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse
from wagtail.blocks import StreamBlockValidationError, StructBlockValidationError
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page
from wagtail.rich_text import RichText
from wagtail_localize.segments.extract import extract_segments

from demo.models import DemoPage
from orion.core.blocks import (
    ContentStreamBlock,
    HeroBlock,
    HighlightedTitleBlock,
    ImageContentBlock,
    RichTextBodyBlock,
)
from orion.core.blocks.content import BlockStyleSelect
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
]


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


def _tags(html, tag):
    return re.findall(rf"<{tag}\b[^>]*>", html)


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

        assert layout.children == ["title", "intro", "buttons", "image"]
        assert layout.settings == ["style", "is_visible"]


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

        for tag in _tags(html, "img"):
            assert "srcset=" in tag
            assert ".webp" in tag
            assert 'width="' in tag
            assert 'height="' in tag
            assert 'loading="lazy"' in tag

    def test_hero_image_loads_immediately(self, render, image_value):
        html = render(("hero", {"title": "<p>T</p>", "image": image_value}))

        assert 'loading="lazy"' not in _tags(html, "img")[0]

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
