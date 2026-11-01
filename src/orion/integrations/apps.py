from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IntegrationsConfig(AppConfig):
    name = "orion.integrations"
    label = "orion_integrations"
    verbose_name = _("Integrations")
    default_auto_field = "django.db.models.BigAutoField"
