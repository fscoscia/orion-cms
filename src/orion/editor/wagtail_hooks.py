from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.userbar import BaseItem
from wagtail.models import Locale

from orion.editor import views
from orion.editor.colors import get_admin_colors
from orion.editor.home import WelcomePanel, get_article_listings

# Wagtail's menu items that only administrators use (roles arrive in change 3).
ADMIN_ONLY_MENU_ITEMS = {"reports", "help"}


@hooks.register("construct_homepage_panels")
def add_welcome_panel(request, panels):
    panels.insert(0, WelcomePanel())


# Runs last: Wagtail's image and document apps add their counters after Orion's apps.
@hooks.register("construct_homepage_summary_items", order=100)
def remove_summary_counters(request, items):
    # The welcome panel replaces the page, image and document counters.
    items.clear()


@hooks.register("register_admin_urls")
def register_editor_urls():
    return [
        path("orion/new-article/", views.new_article, name="orion_editor_new_article")
    ]


@hooks.register("insert_global_admin_css")
def editor_css():
    links = [static("orion/editor/admin.css")]
    if get_admin_colors():
        links.append(reverse("orion_admin_colors"))
    return format_html(
        "".join('<link rel="stylesheet" href="{}">' for _link in links), *links
    )


class NewArticleMenuItem(MenuItem):
    def is_shown(self, request):
        return bool(get_article_listings(request.user))


@hooks.register("register_admin_menu_item")
def new_article_menu_item():
    return NewArticleMenuItem(
        _("New article"),
        reverse("orion_editor_new_article"),
        name="orion_new_article",
        icon_name="plus",
        order=1,
    )


@hooks.register("register_admin_menu_item")
def view_site_menu_item():
    return MenuItem(
        _("View the site"),
        "/",
        name="orion_view_site",
        icon_name="globe",
        order=100000,
        attrs={"target": "_blank", "rel": "noopener"},
    )


@hooks.register("construct_main_menu")
def hide_admin_only_items(request, menu_items):
    if not request.user.is_superuser:
        menu_items[:] = [
            item for item in menu_items if item.name not in ADMIN_ONLY_MENU_ITEMS
        ]


class LinkItem(BaseItem):
    """A link in the site's floating bar."""

    template_name = "orion/editor/userbar_item.html"

    def __init__(self, label, url, icon):
        self.label, self.url, self.icon = label, url, icon

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context.update(label=self.label, url=self.url, icon=self.icon)
        return context


def _snippet_url(model, user, instance):
    """Edit the instance, or create it in the active language when it is missing."""
    app_label, model_name = model._meta.app_label, model._meta.model_name
    namespace = f"wagtailsnippets_{app_label}_{model_name}"
    if instance is not None and user.has_perm(f"{app_label}.change_{model_name}"):
        return reverse(f"{namespace}:edit", args=[instance.pk])
    if instance is None and user.has_perm(f"{app_label}.add_{model_name}"):
        return (
            f"{reverse(f'{namespace}:add')}?locale={Locale.get_active().language_code}"
        )
    return None


@hooks.register("construct_wagtail_userbar")
def add_header_and_footer_items(request, items, page):
    # Imported here: models load after this module during app setup.
    from orion.navigation.models import Menu, MenuLocation
    from orion.site_data.models import SiteTexts

    locale = Locale.get_active()
    user = request.user
    links = []
    for label, location, icon in (
        (_("Header"), MenuLocation.HEADER, "list-ul"),
        (_("Footer"), MenuLocation.FOOTER, "list-ul"),
    ):
        menu = Menu.objects.filter(location=location, locale=locale).first()
        url = _snippet_url(Menu, user, menu)
        if url and menu is None:
            url += f"&location={location}"
        links.append((label, url, icon))
    texts = SiteTexts.objects.filter(locale=locale).first()
    links.append((_("Footer texts"), _snippet_url(SiteTexts, user, texts), "pilcrow"))
    items.extend(LinkItem(label, url, icon) for label, url, icon in links if url)
