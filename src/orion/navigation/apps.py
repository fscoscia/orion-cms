from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NavigationConfig(AppConfig):
    name = "orion.navigation"
    label = "orion_navigation"
    verbose_name = _("Navigation")
    default_auto_field = "django.db.models.BigAutoField"
