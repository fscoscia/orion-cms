from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SnippetsConfig(AppConfig):
    name = "orion.snippets"
    label = "orion_snippets"
    verbose_name = _("Code snippets")
    default_auto_field = "django.db.models.BigAutoField"
