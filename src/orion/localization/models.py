from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting


@register_setting(icon="globe")
class LanguageSettings(BaseGenericSetting):
    """Which of the site's languages visitors can see.

    A language added in the admin can be edited right away; it is shown to visitors
    only once it is marked here. The base language is always public.
    """

    public_locales = models.ManyToManyField(
        "wagtailcore.Locale",
        blank=True,
        related_name="+",
        verbose_name=_("public languages"),
        help_text=_(
            "Visitors only see content in these languages. The base language is "
            "always public."
        ),
    )

    panels = [
        FieldPanel("public_locales", widget=forms.CheckboxSelectMultiple),
    ]

    class Meta:
        verbose_name = _("languages")
