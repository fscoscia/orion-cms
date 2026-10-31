from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FormsConfig(AppConfig):
    name = "orion.forms"
    label = "orion_forms"
    verbose_name = _("Forms")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Importing the module registers its system checks with Django.
        from orion.forms import checks  # noqa: F401
