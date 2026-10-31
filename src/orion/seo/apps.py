from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SeoConfig(AppConfig):
    name = "orion.seo"
    label = "orion_seo"
    verbose_name = _("SEO")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from orion.seo import signals  # noqa: F401
