"""The admin home's welcome panel: greeting, common tasks and unpublished changes."""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail.admin.ui.components import Component
from wagtail.models import Locale, Site
from wagtail.permission_policies.pages import PagePermissionPolicy

UNPUBLISHED_CHANGES_LIMIT = 8


def get_home_page():
    """The default site's home page, in the base language."""
    site = Site.objects.filter(is_default_site=True).select_related("root_page").first()
    return site.root_page.specific if site else None


def get_article_listings(user):
    """Article listings in the base language where the user can add articles."""
    # Imported here: page models import the blocks that this app's hooks may load first.
    from orion.pages.models import ArticleIndexPage

    return [
        listing
        for listing in ArticleIndexPage.objects.filter(locale=Locale.get_default())
        .order_by("path")
        .specific()
        if listing.permissions_for_user(user).can_add_subpage()
    ]


def get_actions(user):
    """The big actions of the welcome panel the user can take, as dicts."""
    from orion.site_data.models import SiteSettings

    actions = []
    home_page = get_home_page()
    home_permissions = home_page.permissions_for_user(user) if home_page else None
    if home_permissions and home_permissions.can_add_subpage():
        actions.append(
            {
                "url": reverse("wagtailadmin_pages:add_subpage", args=[home_page.pk]),
                "icon": "doc-empty-inverse",
                "title": _("Create a page"),
                "description": _("A new page for the site, with blocks."),
            }
        )
    if get_article_listings(user):
        actions.append(
            {
                "url": reverse("orion_editor_new_article"),
                "icon": "doc-full",
                "title": _("Write an article"),
                "description": _("News or a blog post."),
            }
        )
    if home_permissions and home_permissions.can_edit():
        actions.append(
            {
                "url": reverse("wagtailadmin_pages:edit", args=[home_page.pk]),
                "icon": "home",
                "title": _("Edit the home page"),
                "description": _("Texts, photos and buttons of the home page."),
            }
        )
    if user.has_perm("wagtailimages.add_image"):
        actions.append(
            {
                "url": reverse("wagtailimages:add_multiple"),
                "icon": "image",
                "title": _("Upload images"),
                "description": _("Drag several at once."),
            }
        )
    if user.has_perm("orion_navigation.change_menu"):
        actions.append(
            {
                "url": reverse("wagtailsnippets_orion_navigation_menu:list"),
                "icon": "list-ul",
                "title": _("Menus"),
                "description": _("The header and footer menus."),
            }
        )
    if user.has_perm("orion_site_data.change_sitesettings"):
        actions.append(
            {
                "url": reverse(
                    "wagtailsettings:edit",
                    args=["orion_site_data", "sitesettings", SiteSettings.load().pk],
                ),
                "icon": "site",
                "title": _("Site data"),
                "description": _("Logo, contact details and social networks."),
            }
        )
    return actions


def get_unpublished_changes(user):
    """Pages the user can edit that have changes not published yet, newest first."""
    return (
        PagePermissionPolicy()
        .instances_user_has_permission_for(user, "change")
        .filter(has_unpublished_changes=True, depth__gt=1)
        .order_by("-latest_revision_created_at")
        .specific()[:UNPUBLISHED_CHANGES_LIMIT]
    )


class WelcomePanel(Component):
    name = "orion_welcome"
    template_name = "orion/editor/home/welcome_panel.html"
    order = 10

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        user = parent_context["request"].user
        context["user"] = user
        context["actions"] = get_actions(user)
        context["unpublished_pages"] = get_unpublished_changes(user)
        return context
