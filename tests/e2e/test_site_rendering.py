import datetime
from pathlib import Path

import pytest
from django.core.files import File
from django.utils import timezone
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


class TestCountdown:
    def _countdown(self, delta, **extra):
        deadline = (timezone.now() + delta).isoformat()
        return ("countdown", {"title": "<p>Cierre</p>", "deadline": deadline, **extra})

    def test_clock_shows_the_time_left_and_ticks(self, live_server_page, home_page):
        page = _publish_body(
            home_page,
            "cuenta",
            self._countdown(datetime.timedelta(days=3, hours=2, minutes=5)),
        )
        errors = _record_errors(live_server_page)

        live_server_page.goto(page.url)
        clock = live_server_page.locator(".orion-countdown__clock")
        clock.wait_for(state="visible")
        units = live_server_page.locator(".orion-countdown__unit strong")
        assert units.nth(0).text_content() == "3"
        assert units.nth(1).text_content() == "02"
        first = units.nth(3).text_content()
        live_server_page.wait_for_function(
            "first => document.querySelectorAll("
            "'.orion-countdown__unit strong')[3].textContent !== first",
            arg=first,
        )
        assert not [error for error in errors if "Content Security" in error]

    def test_passed_deadline_shows_the_message(self, live_server_page, home_page):
        page = _publish_body(
            home_page,
            "cerrada",
            self._countdown(
                -datetime.timedelta(days=1), closed_message="Postulaciones cerradas"
            ),
        )

        live_server_page.goto(page.url)

        closed = live_server_page.locator(".orion-countdown__closed")
        closed.wait_for(state="visible")
        assert not live_server_page.locator(".orion-countdown__clock").is_visible()

    def test_passed_deadline_without_a_message_shows_zeros(
        self, live_server_page, home_page
    ):
        page = _publish_body(
            home_page, "ceros", self._countdown(-datetime.timedelta(days=1))
        )

        live_server_page.goto(page.url)

        units = live_server_page.locator(".orion-countdown__unit strong")
        units.first.wait_for(state="visible")
        assert [units.nth(index).text_content() for index in range(4)] == [
            "0",
            "00",
            "00",
            "00",
        ]

    def test_without_javascript_the_date_is_shown(
        self, browser, live_server, home_page
    ):
        page = _publish_body(
            home_page, "sin-js-cuenta", self._countdown(datetime.timedelta(days=3))
        )
        context = browser.new_context(java_script_enabled=False)
        visitor = context.new_page()

        visitor.goto(f"{live_server.url}{page.url}")

        assert not visitor.locator(".orion-countdown__clock").is_visible()
        assert (
            str(timezone.now().year + 0)
            in visitor.locator(".orion-countdown").text_content()
        )
        context.close()


class TestMarquee:
    def _marquee(self):
        return ("marquee", {"phrases": ["Movilidad", "Logística", "Economía"]})

    def _animation(self, page, property_name):
        return page.locator(".orion-marquee__track").evaluate(
            f"track => getComputedStyle(track).{property_name}"
        )

    def test_slides_pauses_and_resumes(self, live_server_page, home_page):
        page = _publish_body(home_page, "cinta", self._marquee())
        errors = _record_errors(live_server_page)

        live_server_page.goto(page.url)
        toggle = live_server_page.locator(".orion-marquee__toggle")
        toggle.wait_for(state="visible")
        assert self._animation(live_server_page, "animationName") == "orion-marquee"
        assert self._animation(live_server_page, "animationPlayState") == "running"

        toggle.click()
        live_server_page.mouse.move(0, 0)
        assert toggle.get_attribute("aria-pressed") == "true"
        assert self._animation(live_server_page, "animationPlayState") == "paused"

        toggle.click()
        live_server_page.mouse.move(0, 0)
        assert toggle.get_attribute("aria-pressed") == "false"
        assert self._animation(live_server_page, "animationPlayState") == "running"
        assert not [error for error in errors if "Content Security" in error]

    def test_the_pointer_over_the_marquee_pauses_it(self, live_server_page, home_page):
        page = _publish_body(home_page, "cinta-puntero", self._marquee())

        live_server_page.goto(page.url)
        live_server_page.locator(".orion-marquee__toggle").wait_for(state="visible")
        live_server_page.locator(".orion-marquee__viewport").hover()

        assert self._animation(live_server_page, "animationPlayState") == "paused"

    def test_reduced_motion_keeps_it_still_without_a_button(
        self, live_server_page, home_page
    ):
        page = _publish_body(home_page, "cinta-quieta", self._marquee())
        live_server_page.emulate_media(reduced_motion="reduce")

        live_server_page.goto(page.url)
        live_server_page.wait_for_timeout(300)

        assert self._animation(live_server_page, "animationName") == "none"
        assert not live_server_page.locator(".orion-marquee__toggle").is_visible()
        copy = live_server_page.locator(".orion-marquee__group--copy")
        assert not copy.is_visible()
        assert live_server_page.get_by_text("Economía").first.is_visible()

    def test_without_javascript_it_is_still(self, browser, live_server, home_page):
        page = _publish_body(home_page, "cinta-sin-js", self._marquee())
        context = browser.new_context(java_script_enabled=False)
        visitor = context.new_page()

        visitor.goto(f"{live_server.url}{page.url}")

        assert not visitor.locator(".orion-marquee__toggle").is_visible()
        assert not visitor.locator(".orion-marquee__group--copy").is_visible()
        assert visitor.get_by_text("Movilidad").first.is_visible()
        context.close()


class TestReveal:
    """Blocks that appear as they enter the screen (ORION_BLOCK_REVEAL)."""

    def _tall_page(self, home_page, slug):
        # Enough height that the later blocks start well below the first screen.
        tall = "<p>" + "Texto largo. " * 400 + "</p>"
        blocks = [("text", {"body": tall}) for _ in range(4)]
        return _publish_body(home_page, slug, *blocks)

    def _is_hidden(self, page, index):
        return (
            page.locator("[data-reveal]")
            .nth(index)
            .evaluate("block => getComputedStyle(block).opacity === '0'")
        )

    def _wait_until_visible(self, page, index):
        # The fade takes a moment: opacity is still 0 when the class is added.
        page.wait_for_function(
            "index => getComputedStyle("
            "document.querySelectorAll('[data-reveal]')[index]).opacity === '1'",
            arg=index,
        )

    def test_blocks_below_the_fold_wait_and_then_appear(
        self, live_server_page, home_page, settings
    ):
        settings.ORION_BLOCK_REVEAL = True
        page = self._tall_page(home_page, "revelar")
        errors = _record_errors(live_server_page)
        # Revealing moves blocks with transform only: no layout shift.
        live_server_page.add_init_script(
            "window.__shift = 0;"
            "new PerformanceObserver((list) => {"
            " for (const entry of list.getEntries()) {"
            "  if (!entry.hadRecentInput) window.__shift += entry.value; } })"
            ".observe({ type: 'layout-shift', buffered: true });"
        )

        live_server_page.goto(page.url)
        live_server_page.wait_for_timeout(300)
        assert self._is_hidden(live_server_page, 2)
        # The first block is never marked: it is there from the start.
        assert live_server_page.locator(".block-text").first.evaluate(
            "block => getComputedStyle(block).opacity === '1'"
        )

        live_server_page.locator("[data-reveal]").nth(2).scroll_into_view_if_needed()
        live_server_page.wait_for_function(
            "() => document.querySelectorAll('[data-reveal]')[2]"
            ".classList.contains('is-revealed')"
        )
        self._wait_until_visible(live_server_page, 2)
        assert live_server_page.evaluate("window.__shift") < 0.01
        assert not [error for error in errors if "Content Security" in error]

    def test_nothing_is_hidden_with_reduced_motion(
        self, live_server_page, home_page, settings
    ):
        settings.ORION_BLOCK_REVEAL = True
        page = self._tall_page(home_page, "revelar-quieto")
        live_server_page.emulate_media(reduced_motion="reduce")

        live_server_page.goto(page.url)
        live_server_page.wait_for_timeout(300)

        assert not self._is_hidden(live_server_page, 2)
        assert not self._is_hidden(live_server_page, 1)

    def test_nothing_is_hidden_without_javascript(
        self, browser, live_server, home_page, settings
    ):
        settings.ORION_BLOCK_REVEAL = True
        page = self._tall_page(home_page, "revelar-sin-js")
        context = browser.new_context(java_script_enabled=False)
        visitor = context.new_page()

        visitor.goto(f"{live_server.url}{page.url}")

        for index in range(3):
            assert (
                visitor.locator("[data-reveal]")
                .nth(index)
                .evaluate("block => getComputedStyle(block).opacity === '1'")
            )
        context.close()

    def test_everything_shows_if_the_observer_never_answers(
        self, live_server_page, home_page, settings
    ):
        settings.ORION_BLOCK_REVEAL = True
        page = self._tall_page(home_page, "revelar-sin-observador")
        live_server_page.add_init_script(
            "window.IntersectionObserver = class {"
            " observe() {} unobserve() {} disconnect() {} };"
        )

        live_server_page.goto(page.url)
        live_server_page.wait_for_timeout(300)
        assert self._is_hidden(live_server_page, 2)

        live_server_page.wait_for_function(
            "() => document.querySelectorAll('[data-reveal]:not(.is-revealed)')"
            ".length === 0",
            timeout=6000,
        )
        self._wait_until_visible(live_server_page, 2)

    def test_setting_off_changes_nothing(self, live_server_page, home_page):
        page = self._tall_page(home_page, "sin-revelar")

        live_server_page.goto(page.url)

        assert live_server_page.locator("[data-reveal]").count() == 0
