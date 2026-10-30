from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import StreamField
from wagtail.models import Locale, TranslatableMixin
from wagtail.snippets.models import register_snippet

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
    phone = models.CharField(_("phone"), max_length=30, blank=True)
    whatsapp = models.CharField(_("WhatsApp"), max_length=30, blank=True)
    email = models.EmailField(_("email"), blank=True)
    address = models.TextField(_("address"), blank=True)
    social_links = StreamField(
        [("social_link", SocialLinkBlock())],
        blank=True,
        verbose_name=_("social networks"),
    )

    edit_handler = TabbedInterface(
        [
            ObjectList(
                [FieldPanel("logo"), FieldPanel("footer_logo")], heading=_("Identity")
            ),
            ObjectList(
                [
                    FieldPanel("phone"),
                    FieldPanel("whatsapp"),
                    FieldPanel("email"),
                    FieldPanel("address"),
                ],
                heading=_("Contact"),
            ),
            ObjectList([FieldPanel("social_links")], heading=_("Social networks")),
        ]
    )

    class Meta:
        verbose_name = _("site data")


@register_snippet
class SiteTexts(TranslatableMixin, models.Model):
    """Site-wide texts that are translated: one version per language."""

    tagline = models.CharField(_("tagline"), max_length=160, blank=True)
    legal_text = models.TextField(
        _("legal text"),
        blank=True,
        help_text=_("Shown at the bottom of the footer, for example the copyright."),
    )

    panels = [FieldPanel("tagline"), FieldPanel("legal_text")]

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
