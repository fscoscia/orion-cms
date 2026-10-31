from django.urls import path
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.ui.menus.pages import PageMenuItem

from orion.forms import admin_views
from orion.forms.models import FormPage


@hooks.register("register_admin_urls")
def register_form_urls():
    return [
        path(
            "orion/forms/submissions/<int:submission_id>/files/<str:field_name>/",
            admin_views.attachment,
            name="orion_form_attachment",
        ),
        path(
            "orion/forms/<int:page_id>/test-email/",
            admin_views.test_email,
            name="orion_form_test_email",
        ),
    ]


class TestEmailButton(PageMenuItem):
    label = _("Send a test email")
    icon_name = "mail"
    url_name = "orion_form_test_email"

    def is_shown(self, user):
        return self.page.permissions_for_user(user).can_edit()


@hooks.register("register_page_header_buttons")
def test_email_button(page, user, view_name, next_url=None):
    if page.specific_class and issubclass(page.specific_class, FormPage):
        yield TestEmailButton(page=page, priority=67)
