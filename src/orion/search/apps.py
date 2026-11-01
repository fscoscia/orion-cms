from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SearchConfig(AppConfig):
    name = "orion.search"
    label = "orion_search"
    verbose_name = _("Site search")
    default_auto_field = "django.db.models.BigAutoField"
