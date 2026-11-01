from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from orion.editor.roles import is_site_administrator
from orion.search import admin_views


@hooks.register("register_admin_urls")
def register_search_urls():
    return [path("orion/searches/", admin_views.report, name="orion_search_report")]


class AdministratorMenuItem(MenuItem):
    def is_shown(self, request):
        return is_site_administrator(request.user)


@hooks.register("register_reports_menu_item")
def search_report_menu_item():
    return AdministratorMenuItem(
        _("Searches"),
        reverse("orion_search_report"),
        name="orion_searches",
        icon_name="search",
        order=960,
    )
