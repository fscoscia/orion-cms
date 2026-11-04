from pathlib import Path

import pytest
from django.core.files import File
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from orion.core.blocks import ContentStreamBlock
from orion.navigation.models import Menu, MenuLocation
from orion.pages.models import ContentPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.django_db(transaction=True, serialized_rollback=True),
]


def _publish_tabs_page(home_page, slug):
    """A published child page whose body is a two-tab `tabs` block."""
    stream_block = ContentStreamBlock()
    raw = [
        {
            "type": "tabs",
            "value": {
                "tabs": [
                    {"title": "Primera pestaña", "body": "<p>Contenido uno.</p>"},
                    {"title": "Segunda pestaña", "body": "<p>Contenido dos.</p>"},
                ]
            },
        }
    ]
    body = stream_block.clean(stream_block.to_python(raw))
    page = home_page.add_child(
        instance=ContentPage(title="Con pestañas", slug=slug, body=body)
    )
    page.save_revision().publish()
    return page


class TestAlpineUnderCsp:
    def test_tabs_component_initializes_and_switches_panels(
        self, live_server_page, home_page
    ):
        console_errors = []
        live_server_page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )

        page = _publish_tabs_page(home_page, "con-pestanas")
        live_server_page.goto(page.url)

        tablist = live_server_page.locator('[role="tablist"]')
        panels = live_server_page.locator(".orion-tabs__panel")

        # Alpine's `init()` removes the no-JS fallback's `hidden` from the tablist,
        # and hides every panel but the first: it only ran if the CSP let it.
        assert tablist.is_visible()
        assert panels.nth(0).is_visible()
        assert not panels.nth(1).is_visible()

        live_server_page.locator('[role="tab"]').nth(1).click()

        assert not panels.nth(0).is_visible()
        assert panels.nth(1).is_visible()

        csp_errors = [
            message
            for message in console_errors
            if "content security policy" in message.lower()
        ]
        assert csp_errors == []


class TestNavigation:
    def test_clicking_a_menu_link_reaches_the_other_page(
        self, live_server_page, home_page, services_page
    ):
        Menu.objects.create(
            location=MenuLocation.HEADER,
            items=[
                {
                    "type": "item",
                    "value": {
                        "link": {"page": services_page.pk},
                        "subitems": [],
                    },
                }
            ],
        )

        live_server_page.goto(home_page.url)
        live_server_page.get_by_role("link", name=services_page.title).click()

        assert live_server_page.url.rstrip("/").endswith(services_page.slug)


# WebM: Playwright's Chromium does not include the codecs of MP4.
SAMPLE_VIDEO = Path(__file__).parent / "sample.webm"


def _publish_body(home_page, slug, *blocks):
    stream_block = ContentStreamBlock()
    raw = [{"type": block_type, "value": value} for block_type, value in blocks]
    body = stream_block.clean(stream_block.to_python(raw))
    page = home_page.add_child(
        instance=ContentPage(title="Medios", slug=slug, body=body)
    )
    page.save_revision().publish()
    return page


@pytest.fixture
def media(settings, tmp_path, live_server_page):
    settings.MEDIA_ROOT = tmp_path
    # The test server does not serve media files.
    live_server_page.route(
        "**/*.webm",
        lambda route: route.fulfill(path=SAMPLE_VIDEO, content_type="video/webm"),
    )
    image = Image.objects.create(
        title="Foto", file=get_test_image_file(size=(1600, 900))
    )
    video = Document.objects.create(
        title="Clip", file=File(SAMPLE_VIDEO.open("rb"), name="clip.webm")
    )
    return {
        "video": video,
        "image": {"image": image.pk, "alt_text": "Una foto", "decorative": False},
    }


def _record_errors(page):
    errors = []
    page.on(
        "console",
        lambda message: (
            errors.append(message.text) if message.type == "error" else None
        ),
    )
    return errors


def _is_playing(page):
    return page.locator("video").first.evaluate("video => !video.paused")


class TestVideo:
    def _ambient(self, media):
        return (
            "video",
            {
                "video": media["video"].pk,
                "cover": media["image"],
                "mode": "ambient",
            },
        )

    def test_video_below_the_fold_is_not_requested(
        self, live_server_page, home_page, media
    ):
        spacer = ("text", {"body": "<p>Texto</p>" * 200})
        page = _publish_body(home_page, "abajo", spacer, self._ambient(media))
        requests = []
        live_server_page.on("request", lambda request: requests.append(request.url))

        live_server_page.goto(page.url)
        live_server_page.wait_for_timeout(300)

        assert not any(url.endswith(".webm") for url in requests)

    def test_ambient_video_plays_only_on_screen(
        self, live_server_page, home_page, media
    ):
        spacer = ("text", {"body": "<p>Texto</p>" * 200})
        page = _publish_body(home_page, "ambiente", self._ambient(media), spacer)
        errors = _record_errors(live_server_page)

        live_server_page.goto(page.url)
        live_server_page.wait_for_function(
            "() => !document.querySelector('video').paused"
        )

        live_server_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        live_server_page.wait_for_function(
            "() => document.querySelector('video').paused"
        )

        live_server_page.evaluate("window.scrollTo(0, 0)")
        live_server_page.wait_for_function(
            "() => !document.querySelector('video').paused"
        )
        assert not [error for error in errors if "Content Security" in error]

    def test_visitor_starts_a_video_from_its_cover(
        self, live_server_page, home_page, media
    ):
        block = (
            "video",
            {"video": media["video"].pk, "cover": media["image"]},
        )
        page = _publish_body(home_page, "controles", block)

        live_server_page.goto(page.url)
        player = live_server_page.locator("video")
        play = live_server_page.locator(".orion-video__play")
        assert play.is_visible() and not player.is_visible()

        play.click()

        live_server_page.wait_for_function(
            "() => !document.querySelector('video').paused"
        )
        assert player.is_visible() and not play.is_visible()
        assert not player.evaluate("video => video.muted")

    def test_visitor_can_pause_an_ambient_video(
        self, live_server_page, home_page, media
    ):
        page = _publish_body(home_page, "pausa", self._ambient(media))

        live_server_page.goto(page.url)
        live_server_page.wait_for_function(
            "() => !document.querySelector('video').paused"
        )
        live_server_page.locator(".orion-video__toggle").click()

        assert not _is_playing(live_server_page)
        toggle = live_server_page.locator(".orion-video__toggle")
        assert toggle.get_attribute("aria-pressed") == "true"

    def test_reduced_motion_keeps_the_cover(self, live_server_page, home_page, media):
        page = _publish_body(home_page, "calma", self._ambient(media))
        live_server_page.emulate_media(reduced_motion="reduce")

        live_server_page.goto(page.url)
        live_server_page.wait_for_timeout(300)

        assert not _is_playing(live_server_page)
        assert not live_server_page.locator(".orion-video__toggle").is_visible()


class TestCarousel:
    def _carousel(self, media, **first_slide):
        slides = [
            {"image": media["image"], "title": f"Diapositiva {number}"}
            for number in range(1, 4)
        ]
        slides[0].update(first_slide)
        return ("carousel", {"slides": slides})

    def _left(self, page):
        return page.locator(".orion-carousel__track").evaluate("t => t.scrollLeft")

    def _wait_for_slide(self, page, number):
        page.wait_for_function(
            "text => document.querySelector("
            "'.orion-carousel [aria-live]').textContent.includes(text)",
            arg=f"{number} de 3",
        )

    def test_arrows_dots_and_position(self, live_server_page, home_page, media):
        page = _publish_body(home_page, "carrusel", self._carousel(media))
        errors = _record_errors(live_server_page)

        live_server_page.goto(page.url)
        next_button = live_server_page.locator(".orion-carousel__arrow").nth(1)
        assert next_button.is_visible()
        self._wait_for_slide(live_server_page, 1)

        next_button.click()
        self._wait_for_slide(live_server_page, 2)
        assert self._left(live_server_page) > 0

        live_server_page.locator(".orion-carousel__dot").nth(2).click()
        self._wait_for_slide(live_server_page, 3)
        assert next_button.get_attribute("aria-disabled") == "true"
        dot = live_server_page.locator(".orion-carousel__dot").nth(2)
        assert dot.get_attribute("aria-current") == "true"
        assert not [error for error in errors if "Content Security" in error]

    def test_keyboard(self, live_server_page, home_page, media):
        page = _publish_body(home_page, "teclado", self._carousel(media))

        live_server_page.goto(page.url)
        self._wait_for_slide(live_server_page, 1)
        live_server_page.locator(".orion-carousel__track").focus()
        live_server_page.keyboard.press("ArrowRight")

        self._wait_for_slide(live_server_page, 2)

    def test_slide_video_stops_when_its_slide_leaves(
        self, live_server_page, home_page, media
    ):
        page = _publish_body(
            home_page, "con-video", self._carousel(media, video=media["video"].pk)
        )

        live_server_page.goto(page.url)
        live_server_page.wait_for_function(
            "() => !document.querySelector('video').paused"
        )
        live_server_page.locator(".orion-carousel__arrow").nth(1).click()

        live_server_page.wait_for_function(
            "() => document.querySelector('video').paused"
        )

    def test_without_javascript_the_slides_scroll(
        self, browser, live_server, home_page, media
    ):
        page = _publish_body(home_page, "sin-js", self._carousel(media))
        context = browser.new_context(java_script_enabled=False)
        visitor = context.new_page()

        visitor.goto(f"{live_server.url}{page.url}")

        assert not visitor.locator(".orion-carousel__controls").is_visible()
        track = visitor.locator(".orion-carousel__track")
        box = track.bounding_box()
        visitor.mouse.move(box["x"] + 50, box["y"] + 50)
        visitor.mouse.wheel(box["width"], 0)
        visitor.wait_for_timeout(300)
        assert track.evaluate("track => track.scrollLeft") > 0
        context.close()


class TestSectionLinks:
    def test_menu_link_reaches_a_section_from_another_page(
        self, live_server_page, home_page
    ):
        spacer = ("text", {"body": "<p>Texto</p>" * 200})
        target = ("text", {"anchor": "destino", "body": "<p>Sección buscada</p>"})
        page = _publish_body(home_page, "con-secciones", spacer, target)
        other = _publish_body(home_page, "otra", ("text", {"body": "<p>Otra</p>"}))
        Menu.objects.create(
            location=MenuLocation.HEADER,
            items=[
                {
                    "type": "item",
                    "value": {
                        "link": {
                            "label": "Ir a la sección",
                            "page": page.pk,
                            "anchor": "destino",
                        },
                        "subitems": [],
                    },
                }
            ],
        )

        live_server_page.goto(other.url)
        live_server_page.get_by_role("link", name="Ir a la sección").click()

        live_server_page.wait_for_url("**/con-secciones/#destino")
        section = live_server_page.locator("#destino")
        live_server_page.wait_for_function(
            "() => document.getElementById('destino').getBoundingClientRect().top < "
            "window.innerHeight"
        )
        assert section.is_visible()
