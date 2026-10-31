from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import StreamField
from wagtail.models import Locale, TranslatableMixin
from wagtail.snippets.models import register_snippet

from orion.core.forms import LocationWidget, clean_location

CONTACT_FIELDS = ("phone", "whatsapp", "email", "address")

SOCIAL_NETWORK_CHOICES = [
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("linkedin", "LinkedIn"),
    ("x", "X"),
    ("youtube", "YouTube"),
    ("tiktok", "TikTok"),
]


class SocialLinkBlock(blocks.StructBlock):
    network = blocks.ChoiceBlock(label=_("Network"), choices=SOCIAL_NETWORK_CHOICES)
    url = blocks.URLBlock(label=_("Profile URL"))

    class Meta:
        icon = "link-external"
        label = _("Social network")


@register_setting(icon="site")
class SiteSettings(BaseGenericSetting):
    """Identity and contact data that is the same in every language."""

    logo = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("logo"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Without a logo, the header shows the site name."),
    )
    footer_logo = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("footer logo"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Usually a light version for the dark footer."),
    )
    privacy_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name=_("privacy policy page"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Linked from the consent checkbox of every form."),
    )
    phone = models.CharField(_("phone"), max_length=30, blank=True)
    whatsapp = models.CharField(_("WhatsApp"), max_length=30, blank=True)
    email = models.EmailField(_("email"), blank=True)
    address = models.TextField(_("address"), blank=True)
    location = models.JSONField(
        _("location on the map"),
        null=True,
        blank=True,
        help_text=_("Shown on the contact page and in map blocks."),
    )
    map_zoom = models.PositiveSmallIntegerField(
        _("map zoom"),
        default=16,
        validators=[MinValueValidator(1), MaxValueValidator(19)],
        help_text=_("From 1 (the whole world) to 19 (a single building)."),
    )
    social_links = StreamField(
        [("social_link", SocialLinkBlock())],
        blank=True,
        verbose_name=_("social networks"),
    )
    favicon = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("favicon"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("The browser tab icon. A square image of at least 512 × 512 px."),
    )
    social_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("default social image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_(
            "Shown when a page without its own image is shared. 1200 × 630 px "
            "works best."
        ),
    )
    robots_txt = models.TextField(
        _("robots.txt"),
        blank=True,
        help_text=_(
            "Leave empty to let search engines read the whole site except the admin. "
            "The sitemap line is added automatically."
        ),
    )
    google_site_verification = models.CharField(
        _("Google Search Console verification code"),
        max_length=100,
        blank=True,
        validators=[
            RegexValidator(
                r"^[A-Za-z0-9_-]+$",
                _(
                    'Paste only the code: the value of content="..." in the '
                    "verification tag."
                ),
            )
        ],
    )

    edit_handler = TabbedInterface(
        [
            ObjectList(
                [
                    FieldPanel("logo"),
                    FieldPanel("footer_logo"),
                    FieldPanel("privacy_page"),
                ],
                heading=_("Identity"),
            ),
            ObjectList(
                [
                    FieldPanel("phone"),
                    FieldPanel("whatsapp"),
                    FieldPanel("email"),
                    FieldPanel("address"),
                    FieldPanel("location", widget=LocationWidget),
                    FieldPanel("map_zoom"),
                ],
                heading=_("Contact"),
            ),
            ObjectList([FieldPanel("social_links")], heading=_("Social networks")),
            ObjectList(
                [
                    FieldPanel("favicon"),
                    FieldPanel("social_image"),
                    FieldPanel("google_site_verification"),
                    FieldPanel("robots_txt"),
                ],
                heading=_("SEO"),
            ),
        ]
    )

    class Meta:
        verbose_name = _("site data")

    def clean(self):
        super().clean()
        try:
            self.location = clean_location(self.location)
        except ValidationError as error:
            raise ValidationError({"location": error.messages}) from None

    def map_point(self, name=""):
        """The site's location as a map point, or None when it is not set."""
        if not self.location:
            return None
        return {**self.location, "name": name, "description": self.address}

    def contact_items(self, names=CONTACT_FIELDS):
        """Return ``(name, value)`` pairs of the contact fields that are filled in."""
        return [(name, getattr(self, name)) for name in names if getattr(self, name)]


@register_snippet
class SiteTexts(TranslatableMixin, models.Model):
    """Site-wide texts that are translated: one version per language."""

    tagline = models.CharField(_("tagline"), max_length=160, blank=True)
    description = models.TextField(
        _("site description"),
        max_length=300,
        blank=True,
        help_text=_("Shown by search engines for pages without their own description."),
    )
    legal_text = models.TextField(
        _("legal text"),
        blank=True,
        help_text=_("Shown at the bottom of the footer, for example the copyright."),
    )

    panels = [
        FieldPanel("tagline"),
        FieldPanel("description"),
        FieldPanel("legal_text"),
    ]

    class Meta(TranslatableMixin.Meta):
        verbose_name = _("site texts")
        verbose_name_plural = _("site texts")
        constraints = [
            models.UniqueConstraint(
                fields=["locale"],
                name="orion_site_texts_one_per_locale",
                violation_error_message=_(
                    "This language already has its site texts. Edit the existing ones."
                ),
            ),
        ]

    def __str__(self):
        return str(_("Site texts ({language})").format(language=self.locale))

    @classmethod
    def for_active_language(cls):
        """Return the texts for the active language, or the base language's."""
        texts = cls.objects.filter(locale=Locale.get_active()).first()
        if texts is None:
            texts = cls.objects.filter(locale=Locale.get_default()).first()
        return texts
