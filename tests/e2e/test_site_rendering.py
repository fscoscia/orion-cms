import pytest

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
