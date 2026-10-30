from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LocalizationConfig(AppConfig):
    name = "orion.localization"
    label = "orion_localization"
    verbose_name = _("Orion localization")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Importing the module registers its system checks with Django.
        from orion.localization import checks  # noqa: F401
