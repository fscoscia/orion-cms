"""URL routes that Orion provides to every project.

Include this module last in the project's ``ROOT_URLCONF``: Wagtail's page serving
matches any path, so routes added after it would never be reached.
"""

from django.conf import settings
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from orion.core.views import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path(settings.ORION_ADMIN_PATH, include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("", include(wagtail_urls)),
]
