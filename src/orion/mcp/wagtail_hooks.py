from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from orion.editor.roles import is_site_administrator
from orion.mcp import admin


@hooks.register("register_admin_urls")
def register_mcp_urls():
    return [
        path("orion/mcp-keys/", admin.keys_list, name="orion_mcp_keys"),
        path("orion/mcp-keys/new/", admin.key_new, name="orion_mcp_key_new"),
        path(
            "orion/mcp-keys/<int:pk>/revoke/",
            admin.key_revoke,
            name="orion_mcp_key_revoke",
        ),
    ]


class AdministratorMenuItem(MenuItem):
    def is_shown(self, request):
        return is_site_administrator(request.user)


@hooks.register("register_settings_menu_item")
def mcp_keys_menu_item():
    return AdministratorMenuItem(
        _("API keys"),
        reverse("orion_mcp_keys"),
        name="orion_mcp_keys",
        icon_name="key",
        order=910,
    )
