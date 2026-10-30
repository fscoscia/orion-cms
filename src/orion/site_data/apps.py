from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SiteDataConfig(AppConfig):
    name = "orion.site_data"
    label = "orion_site_data"
    verbose_name = _("Site data")
    default_auto_field = "django.db.models.BigAutoField"
