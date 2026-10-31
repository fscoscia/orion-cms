from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PagesConfig(AppConfig):
    name = "orion.pages"
    label = "orion_pages"
    verbose_name = _("Pages")
    default_auto_field = "django.db.models.BigAutoField"
