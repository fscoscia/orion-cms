from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page


class SeoMixin(models.Model):
    """Search engine and social network fields for a page type.

    Add it before ``Page`` in a project's page types to get the same controls as
    Orion's pages.
    """

    social_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("social image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Shown when the page is shared. 1200 × 630 px works best."),
    )
    no_index = models.BooleanField(
        _("do not index"),
        default=False,
        help_text=_("Search engines will not show this page."),
    )
    no_follow = models.BooleanField(
        _("do not follow links"),
        default=False,
        help_text=_("Search engines will not follow the links of this page."),
    )

    promote_panels = [
        *Page.promote_panels,
        MultiFieldPanel(
            [
                FieldPanel("social_image"),
                FieldPanel("no_index"),
                FieldPanel("no_follow"),
            ],
            heading=_("Search engines and social networks"),
        ),
    ]

    class Meta:
        abstract = True

    def get_meta_description(self):
        """The description for search engines; the site's is used when empty."""
        return self.search_description

    def get_social_image(self):
        """The image shown when the page is shared, if any."""
        return self.social_image


class NotFoundPath(models.Model):
    """A path of the site that answered 404, and how often."""

    site = models.ForeignKey(
        "wagtailcore.Site", on_delete=models.CASCADE, verbose_name=_("site")
    )
    path = models.CharField(_("path"), max_length=255)
    hits = models.PositiveIntegerField(_("visits"), default=1)
    first_seen = models.DateTimeField(_("first visit"), auto_now_add=True)
    last_seen = models.DateTimeField(_("last visit"), auto_now=True)

    class Meta:
        verbose_name = _("URL not found")
        verbose_name_plural = _("URLs not found")
        constraints = [
            models.UniqueConstraint(
                fields=["site", "path"], name="orion_seo_unique_not_found_path"
            )
        ]

    def __str__(self):
        return self.path
