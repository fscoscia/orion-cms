from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SiteDataConfig(AppConfig):
    name = "orion.site_data"
    label = "orion_site_data"
    verbose_name = _("Site data")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from wagtail.models import ReferenceIndex

        from orion.site_data.models import SiteSettings

        # Settings are not indexed by default: this lists the logos' usage in the admin
        # and keeps them out of orion_unused_images.
        ReferenceIndex.register_model(SiteSettings)
