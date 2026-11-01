from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from orion.editor.roles import is_site_administrator
from orion.integrations import views
from orion.integrations.home import EmailWarningPanel


@hooks.register("register_admin_urls")
def register_integrations_urls():
    return [path("orion/integrations/", views.integrations, name="orion_integrations")]


class AdministratorMenuItem(MenuItem):
    def is_shown(self, request):
        return is_site_administrator(request.user)


@hooks.register("register_settings_menu_item")
def integrations_menu_item():
    return AdministratorMenuItem(
        _("Integrations"),
        reverse("orion_integrations"),
        name="orion_integrations",
        icon_name="cogs",
        order=900,
    )


@hooks.register("construct_homepage_panels")
def add_email_warning_panel(request, panels):
    panels.append(EmailWarningPanel())
