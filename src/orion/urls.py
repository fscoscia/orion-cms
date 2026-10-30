"""URL routes that Orion provides to every project.

Add these routes to the end of the project's ``ROOT_URLCONF`` instead of including the
module: Django only honours per-language routes at the top level of the root URLconf,
and Wagtail's page serving matches any path, so routes after it would never be reached::

    from orion.urls import urlpatterns as orion_urlpatterns

    urlpatterns = [...]  # the project's own routes
    urlpatterns += orion_urlpatterns
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from orion.core.views import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path(settings.ORION_ADMIN_PATH, include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
]

# Pages of the base language have no prefix; other languages use their code.
urlpatterns += i18n_patterns(
    path("", include(wagtail_urls)),
    prefix_default_language=False,
)
