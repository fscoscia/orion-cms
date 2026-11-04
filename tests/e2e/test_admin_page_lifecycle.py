import pytest
from django.urls import reverse

from orion.pages.models import ContentPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.django_db(transaction=True, serialized_rollback=True),
]


def _log_in(live_server_page, username, password):
    live_server_page.goto(reverse("wagtailadmin_login"))
    live_server_page.fill("#id_username", username)
    live_server_page.fill("#id_password", password)
    live_server_page.click("button[type=submit]")


class TestAdminPageLifecycle:
    def test_editor_creates_and_publishes_a_page(
        self, live_server_page, admin_user, home_page
    ):
        _log_in(live_server_page, admin_user.get_username(), "password")
        live_server_page.wait_for_url("**/admin/")

        add_url = reverse(
            "wagtailadmin_pages:add",
            args=["orion_pages", "contentpage", home_page.id],
        )
        live_server_page.goto(add_url)
        live_server_page.fill("#id_title", "Nuestros servicios")
        # The slug lives in the collapsed "Promote" tab, derived from the title by
        # client-side JS; set it directly instead of racing that JS or switching tabs.
        live_server_page.locator("#id_slug").evaluate(
            "(el, value) => { el.value = value; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); }",
            "nuestros-servicios",
        )

        # "Publish" is a secondary action here (this project enables moderation),
        # collapsed into the footer action menu's dropdown behind "Save draft".
        live_server_page.click("footer.footer button.w-dropdown__toggle")
        live_server_page.wait_for_selector('.tippy-box[data-state="visible"]')
        live_server_page.click('button[name="action-publish"]')
        # The "add page" URL already matches "**/admin/pages/**", so wait for the
        # real navigation away from it instead.
        live_server_page.wait_for_url(lambda url: "/pages/add/" not in url)

        page = ContentPage.objects.get(title="Nuestros servicios")
        live_server_page.goto(page.url)

        assert "Nuestros servicios" in live_server_page.inner_text("body")

    def test_invalid_credentials_show_an_error(self, live_server_page):
        _log_in(live_server_page, "nobody", "wrong-password")

        assert "/admin/login" in live_server_page.url
        assert live_server_page.locator("li.error").count() > 0
