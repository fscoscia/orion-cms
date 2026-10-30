from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Locale, TranslatableMixin
from wagtail.snippets.models import register_snippet

from orion.core.blocks import LinkBlock


class MenuLocation(models.TextChoices):
    HEADER = "header", _("Header")
    FOOTER = "footer", _("Footer")


class MenuItemBlock(blocks.StructBlock):
    """A top-level menu item; its subitems are plain links, so menus have two levels."""

    link = LinkBlock(
        require_destination=False,
        label=_("Item"),
        help_text=_("Without a destination, the item only titles its subitems."),
    )
    subitems = blocks.ListBlock(
        LinkBlock(label=_("Subitem")),
        label=_("Subitems"),
        required=False,
        default=[],
    )

    class Meta:
        icon = "list-ul"
        label = _("Menu item")


@register_snippet
class Menu(TranslatableMixin, models.Model):
    """A navigation menu for one location of the site, in one language."""

    location = models.CharField(
        _("location"), max_length=20, choices=MenuLocation.choices
    )
    items = StreamField(
        [("item", MenuItemBlock())],
        blank=True,
        verbose_name=_("items"),
    )

    panels = [FieldPanel("location"), FieldPanel("items")]

    class Meta(TranslatableMixin.Meta):
        verbose_name = _("menu")
        verbose_name_plural = _("menus")
        constraints = [
            models.UniqueConstraint(
                fields=["location", "locale"],
                name="orion_menu_one_per_location_and_locale",
                violation_error_message=_(
                    "This language already has a menu for this location."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.get_location_display()} ({self.locale})"

    @classmethod
    def for_active_language(cls, location):
        """Return the menu for a location in the active language, or the base one's."""
        menu = cls.objects.filter(location=location, locale=Locale.get_active()).first()
        if menu is None:
            menu = cls.objects.filter(
                location=location, locale=Locale.get_default()
            ).first()
        return menu
