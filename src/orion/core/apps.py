from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    name = "orion.core"
    label = "orion_core"
    verbose_name = _("Orion core")

    def ready(self):
        # Importing the module registers its system checks with Django.
        from orion.core import checks  # noqa: F401
