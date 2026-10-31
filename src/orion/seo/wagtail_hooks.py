from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from orion.editor.roles import is_site_administrator
from orion.seo import admin_views


@hooks.register("register_admin_urls")
def register_not_found_urls():
    return [
        path("orion/not-found/", admin_views.index, name="orion_not_found_index"),
        path(
            "orion/not-found/<int:pk>/redirect/",
            admin_views.create_redirect,
            name="orion_not_found_redirect",
        ),
        path(
            "orion/not-found/<int:pk>/discard/",
            admin_views.discard,
            name="orion_not_found_discard",
        ),
    ]


class AdministratorMenuItem(MenuItem):
    def is_shown(self, request):
        return is_site_administrator(request.user)


@hooks.register("register_reports_menu_item")
def not_found_menu_item():
    return AdministratorMenuItem(
        _("URLs not found"),
        reverse("orion_not_found_index"),
        name="orion_not_found",
        icon_name="warning",
        order=950,
    )
